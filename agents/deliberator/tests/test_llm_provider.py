"""The deliberator's LLM provider is chosen, never guessed (DL-99).

Agent: deliberator
Role: pin provider selection, the per-provider key env var, and the refusal to
      default silently on an unknown name.
External I/O: none — no client is constructed against a real vendor.
"""

from __future__ import annotations

import importlib
import sys
import types
from typing import Any

import pytest

from agents.deliberator.llm_factory import (
    KEY_ENV,
    UnknownProviderError,
    build_llm,
    key_env_var,
)
from agents.deliberator.settings import DeliberatorSettings
from kernel import describe


class _FakeClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key


def _install_fake(monkeypatch: pytest.MonkeyPatch, name: str, attr: str) -> None:
    """Install a stand-in vendor SDK so no real client is built."""
    module = types.ModuleType(name)
    setattr(module, attr, _FakeClient)
    monkeypatch.setitem(sys.modules, name, module)


def _build(provider: str, **over: Any) -> Any:
    kwargs: dict[str, Any] = {
        "api_key": "k",
        "model": "m",
        "max_tokens": 16,
        "effort": "max",
    }
    kwargs.update(over)
    return build_llm(provider, **kwargs)


def test_openai_is_selectable(monkeypatch: pytest.MonkeyPatch) -> None:
    """DL-99: a single-vendor outage must not be able to blind the veto."""
    _install_fake(monkeypatch, "openai", "OpenAI")

    client = _build("openai")

    assert type(client).__name__ == "OpenAILLMClient"
    assert client.model == "m"


def test_anthropic_remains_the_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """The switch is opt-in; nothing changes for an unconfigured deployment."""
    _install_fake(monkeypatch, "anthropic", "Anthropic")

    client = _build("anthropic")

    assert type(client).__name__ == "AnthropicLLMClient"
    assert DeliberatorSettings().llm_provider == "anthropic"


def test_an_unknown_provider_raises_rather_than_defaulting() -> None:
    """Defaulting would silently change who reviewed the trade."""
    with pytest.raises(UnknownProviderError, match="gemini"):
        _build("gemini")


def test_each_provider_reads_its_own_key() -> None:
    assert key_env_var("anthropic") == "ANTHROPIC_API_KEY"
    assert key_env_var("openai") == "OPENAI_API_KEY"
    assert set(KEY_ENV) == {"anthropic", "openai"}


def test_an_unknown_provider_has_no_key_env_var() -> None:
    with pytest.raises(UnknownProviderError):
        key_env_var("gemini")


def test_a_missing_key_fails_before_any_call(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail at construction, not on the first debate turn."""
    _install_fake(monkeypatch, "openai", "OpenAI")

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        _build("openai", api_key=None)


def test_openai_returns_the_assistant_text(monkeypatch: pytest.MonkeyPatch) -> None:
    """The adapter pulls text out of a chat completion and tolerates empties."""
    from agents.deliberator.llm_openai import OpenAILLMClient, _text

    _install_fake(monkeypatch, "openai", "OpenAI")
    client = OpenAILLMClient(api_key="k", model="m")

    empty = types.SimpleNamespace(message=types.SimpleNamespace(content=None))
    said = types.SimpleNamespace(message=types.SimpleNamespace(content="verdict"))
    response = types.SimpleNamespace(choices=[empty, said])

    assert _text(response) == "verdict"
    assert _text(types.SimpleNamespace(choices=[])) == ""
    assert client.max_tokens == 4096


def test_max_tokens_ceiling_is_tunable_above_the_default() -> None:
    row = {item.name: item for item in describe(DeliberatorSettings)}["max_tokens"]

    assert row.default == 4096
    assert row.minimum == 64
    assert row.maximum == 8192


def _hide_sdk(monkeypatch: pytest.MonkeyPatch, missing: str) -> None:
    """Make one vendor SDK unimportable *through the path the adapter uses*.

    Both adapters call `importlib.import_module`, which does **not** route
    through `builtins.__import__` (measured 2026-08-14). Patching builtins left
    the guard unexercised: the assertion passed only in environments where the
    package genuinely was not installed, which is CI and a fresh worktree but
    not a developer machine carrying the extra. There the same test failed and
    the `except ModuleNotFoundError` lines read 93.94 % — the branch was being
    covered by the environment, never by the test.
    """
    real_import_module = importlib.import_module

    def _absent(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == missing:
            raise ModuleNotFoundError(name)
        return real_import_module(name, *args, **kwargs)

    monkeypatch.setattr(importlib, "import_module", _absent)


@pytest.mark.parametrize(
    ("provider", "package"), [("openai", "openai"), ("anthropic", "anthropic")]
)
def test_a_missing_sdk_raises_configuration_error(
    monkeypatch: pytest.MonkeyPatch, provider: str, package: str
) -> None:
    """An absent package is a configuration fault, not an import crash mid-debate."""
    _hide_sdk(monkeypatch, package)

    with pytest.raises(RuntimeError, match=f"{package} package is not installed"):
        _build(provider)
