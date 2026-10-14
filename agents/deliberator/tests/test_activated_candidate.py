"""A15-A18: the role runs on the settings the master handed it.

Agent: deliberator
Role: prove activation timing, request effort and foreign-model refusal.
External I/O: none; activation and SDK construction are stand-ins.
"""

import os
import sys
from types import ModuleType

import pytest

from agents.deliberator.entrypoint import activated_settings, build_role_llm
from agents.deliberator.settings import DeliberatorSettings
from kernel.llm_anthropic import AnthropicLLMClient
from kernel.llm_factory import ModelProviderMismatchError, build_llm
from kernel.llm_openai import OpenAILLMClient


@pytest.fixture(autouse=True)
def isolated_role_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in tuple(os.environ):
        if key.startswith("DELIBERATOR_"):
            monkeypatch.delenv(key)
    for name, constructor in (("anthropic", "Anthropic"), ("openai", "OpenAI")):
        sdk = ModuleType(name)
        setattr(sdk, constructor, lambda **kwargs: object())
        monkeypatch.setitem(sys.modules, name, sdk)


def test_a15_settings_are_read_after_activation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DLIB-DEP-05: the master's config replaces stale image/environment settings."""
    monkeypatch.setenv("DELIBERATOR_LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("DELIBERATOR_EFFORT", "max")
    initial = DeliberatorSettings(_env_file=None, role="opponent")
    calls: list[tuple[str, str, str | None]] = []

    def activate(url: str, identity: str, *, public_key_pem: str | None) -> None:
        calls.append((url, identity, public_key_pem))
        monkeypatch.setenv("DELIBERATOR_LLM_PROVIDER", "openai")
        monkeypatch.setenv("DELIBERATOR_CHALLENGER_MODEL", "gpt-5.5")
        monkeypatch.setenv("DELIBERATOR_EFFORT", "high")

    actual = activated_settings(
        initial, "http://fixture.invalid", "fixture-public", activate
    )
    assert calls == [
        ("http://fixture.invalid", "deliberator-opponent", "fixture-public")
    ]
    assert initial.llm_provider == "anthropic"
    assert actual is not initial
    assert actual.llm_provider == "openai"
    assert actual.challenger_model == "gpt-5.5"
    assert actual.effort == "high"


def test_a16_role_client_uses_handed_over_candidate() -> None:
    """DLIB-DEP-05: a proponent's vendor, model and effort reach its real adapter."""
    settings = DeliberatorSettings(
        _env_file=None,
        role="proponent",
        llm_provider="anthropic",
        defender_model="claude-opus-5",
        effort="xhigh",
    )
    client = build_role_llm(settings, dict.fromkeys(("ANTHROPIC_API_KEY",), "fixture"))
    assert isinstance(client, AnthropicLLMClient)
    assert client.model == "claude-opus-5"
    assert client.effort == "xhigh"
    assert client.max_tokens == settings.max_tokens


@pytest.mark.parametrize("vendor", ["openai", "anthropic"])
def test_a17_empty_effort_sends_none(vendor: str) -> None:
    """DLIB-DEP-05: empty is the default; OpenAI sees None and Anthropic uses max."""
    settings = DeliberatorSettings(_env_file=None, llm_provider=vendor)
    assert settings.effort == ""
    client = build_role_llm(
        settings,
        dict.fromkeys(("OPENAI_API_KEY", "ANTHROPIC_API_KEY"), "fixture"),
    )
    if vendor == "openai":
        assert isinstance(client, OpenAILLMClient)
        assert client.effort is None
    else:
        assert isinstance(client, AnthropicLLMClient)
        assert client.effort == "max"


@pytest.mark.parametrize(
    ("vendor", "model"), [("openai", "claude-opus-5"), ("anthropic", "gpt-5.5")]
)
def test_a18_foreign_vendor_model_is_refused(vendor: str, model: str) -> None:
    """DLIB-NEV-11: another vendor's model never reaches adapter construction."""
    with pytest.raises(ModelProviderMismatchError, match="belongs to"):
        build_llm(vendor, api_key=None, model=model, max_tokens=64, effort=None)
