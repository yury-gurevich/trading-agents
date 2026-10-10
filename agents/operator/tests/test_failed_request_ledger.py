"""Recorded operator completions distinguish requests, replies, and writes.

Agent: operator
Role: guard the ledger outside the request boundary and completion metadata.
External I/O: none; synthetic client and selective graph failures.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from agents.operator.ledger import recorded_completion
from agents.operator.tests.cutoff_helpers import CompletionStub, assert_vendor_row
from agents.operator.tests.failed_request_helpers import assert_failed_row
from kernel import CollectingFaultSink, InMemoryGraphStore
from kernel.errors import fault_boundary
from kernel.llm_outage import is_silent_call

if TYPE_CHECKING:
    from kernel import AgentFault, Node
    from kernel.graph_support import Props


def _record(
    graph: InMemoryGraphStore, llm: CompletionStub, sink: CollectingFaultSink
) -> tuple[Node, str | None, AgentFault | None]:
    boundary = fault_boundary(
        sink,
        agent="operator",
        module="agents.operator.agent",
        capability="explain",
        reraise=False,
    )
    return recorded_completion(
        graph,
        llm,
        boundary,
        correlation_id="failed-ledger",
        model="fixture-model",
        system="system",
        user="question",
        tool_schema={},
    )


def test_s265_b1_failed_request_returns_its_one_fault_and_silent_row() -> None:
    """OPR-FAIL-01 / OPR-STA-03: failure returns the captured fault and recorded row."""
    graph, sink = InMemoryGraphStore(), CollectingFaultSink()
    llm = CompletionStub(failed=True)
    row, raw, fault = _record(graph, llm, sink)
    assert graph.list_nodes("LLMCall") == (row,)
    assert_failed_row(row)
    assert raw is None
    assert len(sink.faults) == 1
    assert fault is not None
    assert fault is sink.faults[0]
    assert fault.source_agent == "operator"
    assert fault.source_module == "agents.operator.agent"
    assert fault.capability == "explain"
    assert fault.error_type == "TimeoutError"
    assert fault.message == "fixture request timed out"
    assert llm.requests == [("system", "question", {})]


def test_s265_b2_reply_retains_text_stop_reason_and_vendor_usage() -> None:
    """OPR-STA-03: complete_recorded retains reply text, stop word and billed usage."""
    graph, sink = InMemoryGraphStore(), CollectingFaultSink()
    llm = CompletionStub(response="finished answer")
    row, raw, fault = _record(graph, llm, sink)
    assert raw == "finished answer"
    assert fault is None
    assert not sink.faults
    assert_vendor_row(row, "completed")
    assert llm.requests == [("system", "question", {})]


@pytest.mark.parametrize("stop", ["max_tokens", "max_output_tokens"])
def test_s265_b3_cutoff_is_not_a_failed_request(stop: str) -> None:
    """OPR-FAIL-04 / OPR-STA-03: a cut-off returns no fault and keeps billed usage."""
    graph, sink = InMemoryGraphStore(), CollectingFaultSink()
    row, raw, fault = _record(graph, CompletionStub(stop, stopped=True), sink)
    assert raw is None
    assert fault is None
    assert not sink.faults
    assert_vendor_row(row, stop)
    assert not is_silent_call(row)


def test_s265_b4_ledger_write_failure_escapes_request_boundary() -> None:
    """OPR-FAIL-03: a ledger write error propagates, without a failed-request fault."""

    class BrokenLedger(InMemoryGraphStore):
        def merge_node(
            self, label: str, key: str, props: Props, *, schema_version: int = 1
        ) -> Node:
            if label == "LLMCall":
                raise OSError("ledger write failed")
            return super().merge_node(label, key, props, schema_version=schema_version)

    graph, sink = BrokenLedger(), CollectingFaultSink()
    llm = CompletionStub()
    with pytest.raises(OSError, match="ledger write failed"):
        _record(graph, llm, sink)
    assert not sink.faults
    assert not graph.list_nodes("LLMCall")
    assert len(llm.requests) == 1
