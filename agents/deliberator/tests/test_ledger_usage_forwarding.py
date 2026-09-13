"""A truncated or refused completion is still billed, so it is still counted.

Agent: deliberator
Role: prove `_LedgerLLM` forwards the provider's usage on the stopped path as
      well as the clean one.
External I/O: none.

🚨 This is the expensive half to get wrong. `effort` is `max`, so a completion
that ends in `max_tokens` has spent its entire output budget *before* raising —
the most costly calls the fleet makes are exactly the ones whose tokens a
success-only capture would drop. S173 Part B's own round lost 4 of 2,961 calls
this way (DL-160).
"""

from __future__ import annotations

import pytest

from agents.deliberator.agent import _LedgerLLM
from kernel import InMemoryGraphStore, LLMCompletionStoppedError
from kernel.llm_tokens import SOURCE_ESTIMATED, SOURCE_VENDOR, LLMUsage


class _StoppingLLM:
    """An LLM that spends its budget and then declares it was truncated."""

    def __init__(self) -> None:
        self.last_stop_reason = "max_tokens"
        self.last_usage = LLMUsage(tokens_in=2400, tokens_out=4096)

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del system, user, tool_schema
        raise LLMCompletionStoppedError(provider="anthropic", stop_reason="max_tokens")


class _SilentLLM:
    """An LLM that answers but reports no usage at all."""

    def __init__(self) -> None:
        self.last_stop_reason = "end_turn"

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del system, user, tool_schema
        return "a three word answer"


def _props(graph: InMemoryGraphStore, key: str) -> dict[str, object]:
    node = graph.get_node("LLMCall", f"llmcall:deliberator-opponent:{key}")
    assert node is not None
    return dict(node.props)


def test_a_truncated_completion_still_records_what_it_burned() -> None:
    """DLIB-OBS-05: the tokens were spent whether or not an answer came back."""
    graph = InMemoryGraphStore()
    ledger = _LedgerLLM(
        graph,
        _StoppingLLM(),
        calling_agent="deliberator-opponent",
        model="claude-opus-5",
        correlation_id="run:USB:challenger:r1",
    )

    with pytest.raises(LLMCompletionStoppedError, match="max_tokens"):
        ledger.complete(system="sys", user="user", tool_schema={})

    props = _props(graph, "run:USB:challenger:r1")
    assert props["tokens_out"] == 4096
    assert props["tokens_in"] == 2400
    assert props["token_source"] == SOURCE_VENDOR
    assert props["stop_reason"] == "max_tokens"


def test_a_provider_that_reports_no_usage_falls_back_and_says_so() -> None:
    """DLIB-OBS-05: the fake LLM in CI has no usage, and must not look measured."""
    graph = InMemoryGraphStore()
    ledger = _LedgerLLM(
        graph,
        _SilentLLM(),
        calling_agent="deliberator-opponent",
        model="claude-opus-5",
        correlation_id="run:USB:challenger:r2",
    )

    assert ledger.complete(system="sys", user="a b", tool_schema={})

    props = _props(graph, "run:USB:challenger:r2")
    assert props["token_source"] == SOURCE_ESTIMATED
    assert props["tokens_out"] == 4
