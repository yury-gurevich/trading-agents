"""Operator store adapter tests.

Agent: operator
Role: cover operator-owned store wrappers over shared kernel ledgers.
External I/O: none.
"""

from __future__ import annotations

from agents.operator.store import write_llm_call
from kernel import InMemoryGraphStore


def test_write_llm_call_records_operator_attribution() -> None:
    """OPR-IDN-02: operator no longer claims generic LLMCall ownership."""
    graph = InMemoryGraphStore()

    first = write_llm_call(
        graph,
        correlation_id="corr-1",
        model="claude-opus-5",
        prompt_hash="prompt",
        response_hash="response",
        tokens_in=3,
        tokens_out=5,
        latency_ms=7,
    )
    second = write_llm_call(
        graph,
        correlation_id="corr-1",
        model="claude-opus-5",
        prompt_hash="prompt",
        response_hash="response",
        tokens_in=3,
        tokens_out=5,
        latency_ms=7,
    )

    assert second is first
    assert first.props["calling_agent"] == "operator"
    assert first.props["stop_reason"] == "unknown"
