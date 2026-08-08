"""The deliberator's LLM provider is chosen, never guessed (DL-99).

Agent: deliberator
Role: pin provider selection, the per-provider key env var, and the refusal to
      default silently on an unknown name.
External I/O: none — no client is constructed against a real vendor.
"""

from __future__ import annotations

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


def test_a_missing_sdk_raises_configuration_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An absent package is a configuration fault, not an import crash mid-debate."""
    import builtins

    real_import = builtins.__import__

    def _no_openai(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "openai":
            raise ModuleNotFoundError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.delitem(sys.modules, "openai", raising=False)
    monkeypatch.setattr(builtins, "__import__", _no_openai)

    with pytest.raises(RuntimeError, match="openai package is not installed"):
        _build("openai")


def test_complete_sends_system_and_user_and_returns_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The adapter maps the port's system/user split onto chat messages."""
    from agents.deliberator.llm_openai import OpenAILLMClient

    sent: dict[str, Any] = {}

    class _Completions:
        def create(self, **kwargs: Any) -> Any:
            sent.update(kwargs)
            return types.SimpleNamespace(
                choices=[
                    types.SimpleNamespace(
                        message=types.SimpleNamespace(content="uphold")
                    )
                ]
            )

    class _SDK:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key
            self.chat = types.SimpleNamespace(completions=_Completions())

    module = types.ModuleType("openai")
    module.OpenAI = _SDK  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "openai", module)

    client = OpenAILLMClient(api_key="k", model="gpt-5.5", max_tokens=32)
    answer = client.complete(system="be terse", user="review this", tool_schema={})

    assert answer == "uphold"
    assert sent["model"] == "gpt-5.5"
    assert sent["max_completion_tokens"] == 32
    assert [m["role"] for m in sent["messages"]] == ["system", "user"]
    assert sent["messages"][0]["content"] == "be terse"
