"""The operator records vendor tokens but deliberately does not cache.

Agent: operator
Role: pin both halves of one decision — operator calls price off the provider's
      own usage like every other call, and their system prompt is *not* marked
      cacheable, because the tool list ahead of it varies per call.
External I/O: none.

Split from `test_operator_llm.py` at its 139-line size.
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

from agents.operator.llm_anthropic import AnthropicLLMClient, _usage


class _FakeMessages:
    def __init__(self) -> None:
        self.kwargs: dict[str, object] = {}

    def create(self, **kwargs: object) -> object:
        self.kwargs = kwargs
        return SimpleNamespace(
            content=[SimpleNamespace(type="tool_use", input={"answer": "ok"})],
            usage=SimpleNamespace(
                input_tokens=820,
                output_tokens=140,
                cache_read_input_tokens=0,
                cache_creation_input_tokens=0,
            ),
        )


class _FakeAnthropic:
    def __init__(self, *, api_key: str) -> None:
        self.api_key = api_key
        self.messages = _FakeMessages()


_MODULE = SimpleNamespace(Anthropic=_FakeAnthropic)


def _client(monkeypatch: pytest.MonkeyPatch) -> AnthropicLLMClient:
    monkeypatch.setattr(importlib, "import_module", lambda _name: _MODULE)
    return AnthropicLLMClient(api_key="key")  # pragma: allowlist secret


def test_operator_calls_carry_the_vendors_own_token_counts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Item 43: the operator shares the ledger, so it shares the correction."""
    client = _client(monkeypatch)

    client.complete(system="s", user="u", tool_schema={})

    assert client.last_usage is not None
    assert client.last_usage.tokens_in == 820
    assert client.last_usage.tokens_out == 140


def test_the_operator_system_prompt_is_sent_unmarked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unlike the deliberator — and the reason is the `tools` list.

    Caching is a prefix match and `tools` renders *ahead* of `system`. The
    operator sends `parse_intent` or `answer_question` depending on
    `tool_schema`, so the prefix changes on the very axis that varies per call:
    a marked system block would write entries nobody reads and pay 1.25x for
    each. This asserts the plain string, so a later "consistency" edit that
    copies the deliberator's marker here has to argue with a test.
    """
    client = _client(monkeypatch)

    client.complete(system="SYSTEM", user="u", tool_schema={})

    assert client._client.messages.kwargs["system"] == "SYSTEM"


def test_a_failed_operator_call_clears_the_previous_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client(monkeypatch)
    client.complete(system="s", user="u", tool_schema={})

    def boom(**kwargs: object) -> object:
        raise RuntimeError("rate limited")

    monkeypatch.setattr(client._client.messages, "create", boom)
    with pytest.raises(RuntimeError, match="rate limited"):
        client.complete(system="s", user="u", tool_schema={})

    assert client.last_usage is None


def test_a_response_without_usage_reports_none() -> None:
    assert _usage(SimpleNamespace(content=[])) is None
