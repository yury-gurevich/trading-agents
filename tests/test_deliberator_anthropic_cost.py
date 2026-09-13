"""The Anthropic adapter claims the cache and records what the vendor billed.

Agent: deliberator
Role: pin the cache marker on the frozen role prompt and the token counts read
      back off the response, for the live nightly debate path.
External I/O: none - the SDK is faked; no vendor is contacted.

Split from `test_deliberator_anthropic.py` at the 200-line hard block. That file
pins stop reasons and text extraction; this one pins cost.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import agents.deliberator.llm_anthropic as anthropic_adapter
from agents.deliberator.llm_anthropic import AnthropicLLMClient


class _FakeMessages:
    def __init__(self) -> None:
        self.kwargs: dict[str, object] = {}

    def create(self, **kwargs: object) -> object:
        self.kwargs = kwargs
        return SimpleNamespace(
            content=(SimpleNamespace(type="text", text="answer"),),
            stop_reason="end_turn",
            usage=SimpleNamespace(
                input_tokens=1731,
                output_tokens=906,
                cache_read_input_tokens=2561,
                cache_creation_input_tokens=0,
            ),
        )


class _FakeAnthropic:
    def __init__(self, *, api_key: str) -> None:
        self.api_key = api_key
        self.messages = _FakeMessages()


def _client(monkeypatch: pytest.MonkeyPatch) -> AnthropicLLMClient:
    monkeypatch.setattr(
        anthropic_adapter.importlib,
        "import_module",
        lambda name: SimpleNamespace(Anthropic=_FakeAnthropic),
    )
    return AnthropicLLMClient(api_key="test-key")  # pragma: allowlist secret


def test_system_prompt_is_sent_as_a_cache_marked_block() -> None:
    """DLIB-OBS-06: the frozen role prompt is offered to the cache every call.

    S173 Part B paid full input price on all 2,957 of its calls with
    `cache_read` at 0 throughout (DL-160) — not because caching was rejected
    but because the marker was never sent.
    """
    block = anthropic_adapter.cacheable_system("ROLE PROMPT")

    assert block == [
        {
            "type": "text",
            "text": "ROLE PROMPT",
            "cache_control": {"type": "ephemeral"},
        }
    ]


def test_live_path_uses_the_five_minute_ttl_not_the_one_hour_ttl() -> None:
    """The nightly debate's requests are seconds apart (84s/order, DL-150).

    A 1h entry would cost 2x to write instead of 1.25x and buy nothing, because
    a read refreshes the 5-minute timer anyway. The batch harness makes the
    opposite call for the opposite reason, and that asymmetry is deliberate.
    """
    (block,) = anthropic_adapter.cacheable_system("ROLE PROMPT")

    assert "ttl" not in block["cache_control"]


def test_vendor_usage_is_captured_from_the_response(monkeypatch) -> None:
    """DLIB-OBS-05: tokens come off the API's own usage block."""
    client = _client(monkeypatch)

    client.complete(system="sys", user="hello", tool_schema={})

    assert client.last_usage is not None
    assert client.last_usage.tokens_in == 1731
    assert client.last_usage.tokens_out == 906
    assert client.last_usage.cache_read_tokens == 2561
    assert client.last_usage.cache_write_tokens == 0


def test_a_failed_call_does_not_leave_the_previous_usage_behind(monkeypatch) -> None:
    """A stale usage would be attributed to the call that never happened."""
    client = _client(monkeypatch)
    client.complete(system="sys", user="hello", tool_schema={})
    assert client.last_usage is not None

    def boom(**kwargs: object) -> object:
        raise RuntimeError("credit balance is too low")

    monkeypatch.setattr(client._client.messages, "create", boom)

    with pytest.raises(RuntimeError, match="credit balance"):
        client.complete(system="sys", user="hello", tool_schema={})

    assert client.last_usage is None


def test_a_response_without_usage_reports_none() -> None:
    """An SDK that withholds usage must degrade to the stamped estimate."""
    assert anthropic_adapter._usage(SimpleNamespace(content=())) is None
