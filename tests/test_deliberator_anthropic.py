"""Anthropic deliberator LLM adapter tests.

Agent: deliberator
Role: cover configuration failure and fake successful Anthropic completions.
External I/O: none.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import agents.deliberator.llm_anthropic as anthropic_adapter
from agents.deliberator.llm_anthropic import AnthropicLLMClient, ConfigurationError
from kernel import LLMCompletionStoppedError


class _FakeMessages:
    def __init__(self) -> None:
        self.kwargs: dict[str, object] = {}

    def create(self, **kwargs: object) -> object:
        self.kwargs = kwargs
        return SimpleNamespace(
            content=(
                SimpleNamespace(type="text", text="first"),
                SimpleNamespace(type="tool", text="ignored"),
                SimpleNamespace(type="text", text="second"),
                SimpleNamespace(type="text", text=""),
            )
        )


class _FakeAnthropic:
    last: _FakeAnthropic | None = None

    def __init__(self, *, api_key: str) -> None:
        self.api_key = api_key
        self.messages = _FakeMessages()
        _FakeAnthropic.last = self


def test_anthropic_client_requires_key() -> None:
    with pytest.raises(ConfigurationError, match="ANTHROPIC_API_KEY"):
        AnthropicLLMClient(api_key=None)


def test_anthropic_client_reports_missing_package(monkeypatch) -> None:
    def missing(name: str) -> object:
        assert name == "anthropic"
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(anthropic_adapter.importlib, "import_module", missing)

    with pytest.raises(ConfigurationError, match="not installed"):
        AnthropicLLMClient(api_key="test-key")  # pragma: allowlist secret


def test_anthropic_client_returns_text_blocks(monkeypatch) -> None:
    monkeypatch.setattr(
        anthropic_adapter.importlib,
        "import_module",
        lambda name: SimpleNamespace(Anthropic=_FakeAnthropic),
    )
    client = AnthropicLLMClient(
        api_key="test-key",  # pragma: allowlist secret
        model="claude-opus-5",
        max_tokens=123,
        effort="high",
    )

    result = client.complete(system="sys", user="hello", tool_schema={})

    assert result == "first\nsecond"
    assert _FakeAnthropic.last is not None
    kwargs = _FakeAnthropic.last.messages.kwargs
    assert kwargs["model"] == "claude-opus-5"
    assert kwargs["max_tokens"] == 123
    assert kwargs["output_config"] == {"effort": "high"}
    assert kwargs["system"] == "sys"
    assert kwargs["messages"] == [{"role": "user", "content": "hello"}]


def test_anthropic_max_tokens_without_text_raises_stop_reason() -> None:
    """DLIB-FAIL-04 / DLIB-NEV-06: truncation is failure, not empty answer."""
    response = SimpleNamespace(
        content=(SimpleNamespace(type="thinking", text="spent budget"),),
        stop_reason="max_tokens",
    )

    with pytest.raises(RuntimeError, match="max_tokens"):
        anthropic_adapter._text(response)


def test_anthropic_refusal_raises_with_guarded_category() -> None:
    """DLIB-FAIL-04 / DLIB-NEV-06: refusal is named separately from truncation."""
    response = SimpleNamespace(
        content=(),
        stop_reason="refusal",
        stop_details=SimpleNamespace(category="policy"),
    )

    with pytest.raises(LLMCompletionStoppedError, match="refusal") as exc:
        anthropic_adapter._text(response)

    assert exc.value.stop_reason == "refusal"
    assert exc.value.category == "policy"

    with pytest.raises(LLMCompletionStoppedError) as uncategorized:
        anthropic_adapter._text(SimpleNamespace(content=(), stop_reason="refusal"))
    assert uncategorized.value.category is None


def test_anthropic_end_turn_can_return_a_genuine_empty_answer() -> None:
    """DLIB-FAIL-04: a normal empty answer is not a provider failure."""
    response = SimpleNamespace(content=(), stop_reason="end_turn", stop_details=None)

    assert anthropic_adapter._text(response) == ""
