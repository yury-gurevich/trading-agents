"""Anthropic operator adapter cut-off regression proofs.

Agent: operator
Role: prove stop metadata and billed usage survive a stopped completion.
External I/O: none; Anthropic SDK replies are injected.
"""

from __future__ import annotations

import json
from typing import cast

import pytest

from agents.operator.tests.cutoff_helpers import (
    PARTIAL_ANSWER,
    scripted_client,
    vendor_reply,
)
from kernel import LLMCompletionStoppedError
from kernel.llm_anthropic import OperatorAnthropicLLMClient
from kernel.llm_tokens import LLMUsage


@pytest.mark.parametrize("with_schema", [False, True])
@pytest.mark.parametrize("partial", [False, True])
def test_a1_anthropic_cutoff_records_metadata_before_raising(
    monkeypatch: pytest.MonkeyPatch, with_schema: bool, partial: bool
) -> None:
    """OPR-STA-03: both tool shapes retain billed tokens before cut-off raises."""
    data: dict[str, object] | None = {"answer": PARTIAL_ANSWER} if partial else None
    client, requests = scripted_client(
        monkeypatch, "anthropic", [vendor_reply("anthropic", "max_tokens", data)]
    )
    assert isinstance(client, OperatorAnthropicLLMClient)

    with pytest.raises(LLMCompletionStoppedError) as stopped:
        client.complete(
            system="system",
            user="question",
            tool_schema={"type": "object"} if with_schema else {},
        )

    assert stopped.value.provider == "anthropic"
    assert stopped.value.stop_reason == "max_tokens"
    assert client.last_stop_reason == "max_tokens"
    assert client.last_usage == LLMUsage(tokens_in=21_133, tokens_out=4096)
    assert len(requests) == 1


@pytest.mark.parametrize("with_schema", [False, True])
def test_a2_finished_anthropic_reply_keeps_its_stop_reason(
    monkeypatch: pytest.MonkeyPatch, with_schema: bool
) -> None:
    """OPR-STA-03: construction is unknown; each finished call keeps tool_use."""
    data: dict[str, object] = {
        "answer": "complete answer",
        "outcome": "intent",
        "family": "status",
    }
    reply = vendor_reply("anthropic", "tool_use", data)
    client, requests = scripted_client(monkeypatch, "anthropic", [reply, reply])
    assert isinstance(client, OperatorAnthropicLLMClient)
    assert client.last_stop_reason == "unknown"
    for _ in range(2):
        raw = client.complete(
            system="system",
            user="question",
            tool_schema={"type": "object"} if with_schema else {},
        )
        assert (json.loads(raw) if with_schema else raw) == (
            data if with_schema else "complete answer"
        )
        assert client.last_stop_reason == "tool_use"
        assert client.last_usage == LLMUsage(tokens_in=21_133, tokens_out=4096)
    assert len(requests) == 2


@pytest.mark.parametrize("with_schema", [False, True])
def test_a3_anthropic_refusal_returns_without_raising(
    monkeypatch: pytest.MonkeyPatch, with_schema: bool
) -> None:
    """OPR-STA-03: a refusal retains its word and the existing empty/tool result."""
    client, requests = scripted_client(
        monkeypatch, "anthropic", [vendor_reply("anthropic", "refusal")]
    )
    assert isinstance(client, OperatorAnthropicLLMClient)
    raw = client.complete(
        system="system",
        user="question",
        tool_schema={"type": "object"} if with_schema else {},
    )
    assert (json.loads(raw) if with_schema else raw) == (
        {"outcome": "refused", "reason": "model returned no tool result"}
        if with_schema
        else ""
    )
    assert client.last_stop_reason == "refusal"
    assert len(requests) == 1


def test_a4_failed_request_clears_anthropic_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OPR-STA-03: a later request failure never reuses a previous stop or usage."""
    failure = TimeoutError("fixture request timed out")
    client, requests = scripted_client(
        monkeypatch,
        "anthropic",
        [vendor_reply("anthropic", "tool_use", {"answer": "ok"}), failure],
    )
    assert isinstance(client, OperatorAnthropicLLMClient)
    client.complete(system="system", user="first", tool_schema={})
    assert client.last_stop_reason == "tool_use"
    assert client.last_usage == LLMUsage(tokens_in=21_133, tokens_out=4096)
    with pytest.raises(TimeoutError) as raised:
        client.complete(system="system", user="second", tool_schema={})
    assert raised.value is failure
    assert client.last_stop_reason == "unknown"
    assert cast("object", client.last_usage) is None
    assert len(requests) == 2
