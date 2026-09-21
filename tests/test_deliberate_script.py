"""Deliberation script model-builder tests.

Agent: tooling
Role: verify real-mode debate and judge clients come from separate env settings.
External I/O: none.
"""

from __future__ import annotations

import pytest
import scripts.deliberate as subject


class _BuiltText:
    """Lightweight replacement for provider adapters."""

    provider = "base"

    def __init__(self, api_key: str, model: str, *, max_tokens: int = 2000) -> None:
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del system, user, tool_schema
        return ""


class _BuiltOpenAI(_BuiltText):
    provider = "openai"


class _BuiltAnthropic(_BuiltText):
    provider = "anthropic"


def _patch_adapters(monkeypatch: pytest.MonkeyPatch) -> None:
    def build(
        provider: str,
        *,
        api_key: str,
        model: str,
        max_tokens: int,
        effort: str | None,
    ) -> _BuiltText:
        del effort
        implementation = _BuiltOpenAI if provider == "openai" else _BuiltAnthropic
        return implementation(api_key, model, max_tokens=max_tokens)

    monkeypatch.setattr(subject, "build_llm", build)


def test_anthropic_effort_defaults_to_max(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_EFFORT", raising=False)
    assert subject.anthropic_effort() == "max"


def test_anthropic_effort_honours_the_env_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ANTHROPIC_EFFORT", " medium ")
    assert subject.anthropic_effort() == "medium"


def test_anthropic_text_sends_effort_to_the_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The script forwards the Anthropic effort level to the kernel factory."""
    monkeypatch.delenv("ANTHROPIC_EFFORT", raising=False)
    sent: dict[str, object] = {}

    def build(provider: str, **kwargs: object) -> _BuiltAnthropic:
        assert provider == "anthropic"
        sent.update(kwargs)
        return _BuiltAnthropic("key", "claude-opus-5")

    monkeypatch.setattr(subject, "build_llm", build)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "key")
    subject._provider_llm("anthropic", "claude-opus-5")

    assert sent["effort"] == "max"


def test_openai_script_leaves_reasoning_effort_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The old OpenAI wrapper did not send a reasoning-effort override."""
    sent: dict[str, object] = {}

    def build(provider: str, **kwargs: object) -> _BuiltOpenAI:
        assert provider == "openai"
        sent.update(kwargs)
        return _BuiltOpenAI("key", "gpt-5.5")

    monkeypatch.setattr(subject, "build_llm", build)
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    subject._provider_llm("openai", "gpt-5.5")

    assert sent["effort"] is None


def test_build_role_llms_defaults_judge_to_anthropic_opus(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_adapters(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.5")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-token")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-token")
    monkeypatch.delenv("DELIBERATION_JUDGE_PROVIDER", raising=False)
    monkeypatch.delenv("DELIBERATION_JUDGE_MODEL", raising=False)

    debate, judge = subject.build_role_llms(True)

    assert isinstance(debate, _BuiltOpenAI)
    assert debate.model == "gpt-5.5"
    assert debate.api_key == "openai-token"  # pragma: allowlist secret
    assert isinstance(judge, _BuiltAnthropic)
    assert judge.model == "claude-opus-4-8"
    assert judge.api_key == "anthropic-token"  # pragma: allowlist secret
    assert judge.max_tokens == 2000
    output = capsys.readouterr().out
    assert "debate OpenAI gpt-5.5" in output
    assert "judge Anthropic claude-opus-4-8" in output


def test_build_role_llms_honours_explicit_judge_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_adapters(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-token")
    monkeypatch.setenv("DELIBERATION_JUDGE_PROVIDER", "openai")
    monkeypatch.setenv("DELIBERATION_JUDGE_MODEL", "gpt-5.5")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-token")

    debate, judge = subject.build_role_llms(True)

    assert isinstance(debate, _BuiltAnthropic)
    assert debate.model == "claude-haiku-4-5-20251001"
    assert isinstance(judge, _BuiltOpenAI)
    assert judge.model == "gpt-5.5"


def test_build_role_llms_missing_judge_key_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_adapters(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.5")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-token")
    monkeypatch.setenv("DELIBERATION_JUDGE_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")

    with pytest.raises(SystemExit, match="ANTHROPIC_API_KEY not set"):
        subject.build_role_llms(True)


def test_build_role_llms_demo_uses_two_fake_clients() -> None:
    debate, judge = subject.build_role_llms(False)

    assert debate is not judge
    assert debate.complete(system="DEFENDER", user="", tool_schema={})
