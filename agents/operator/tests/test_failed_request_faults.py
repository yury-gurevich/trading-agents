"""Non-request faults, graph privacy, and malformed replies keep their semantics.

Agent: operator
Role: distinguish audit failures from model requests and guard graph properties.
External I/O: none; synthetic clients and in-memory graph.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from agents.operator.tests.cutoff_helpers import CompletionStub
from agents.operator.tests.failed_request_helpers import (
    RequestFailure,
    assert_audit,
    assert_failed_row,
    build_agent,
    command,
)
from contracts.operator import ExplainRequest
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from kernel import Node
    from kernel.graph_support import Props


class AuditFailure(InMemoryGraphStore):
    """Raise only for the audit write, outside the graph's own boundary."""

    def merge_node(
        self, label: str, key: str, props: Props, *, schema_version: int = 1
    ) -> Node:
        if label == "CommandAudit":
            raise OSError("audit failure marker")
        return super().merge_node(label, key, props, schema_version=schema_version)


def test_s265_c4_other_fault_keeps_the_old_sentence() -> None:
    """OPR-FAIL-03: an audit failure retains the existing graph-fault refusal."""
    agent, graph, _bus, sink = build_agent(
        CompletionStub(response="{}"), AuditFailure()
    )
    result = agent._interpret(command())
    assert result.outcome == "refused"
    assert result.message.summary == "Operator could not parse the command."
    assert len(sink.faults) == 1
    assert sink.faults[0].error_type == "OSError"
    assert sink.faults[0].message == "audit failure marker"
    assert len(graph.list_nodes("LLMCall")) == 1
    assert not graph.list_nodes("CommandAudit")
    assert not graph.list_nodes("Intent")


def test_s265_c5_failed_request_then_failed_audit_keeps_both_faults() -> None:
    """OPR-FAIL-01 / OPR-FAIL-03: audit failure stays separate from request failure."""
    agent, graph, _bus, sink = build_agent(CompletionStub(failed=True), AuditFailure())
    result = agent._interpret(command())
    assert result.outcome == "refused"
    assert result.message.summary == "Operator could not parse the command."
    assert tuple(fault.error_type for fault in sink.faults) == (
        "TimeoutError",
        "OSError",
    )
    assert tuple(fault.message for fault in sink.faults) == (
        "fixture request timed out",
        "audit failure marker",
    )
    assert all(fault.capability == "interpret" for fault in sink.faults)
    (row,) = graph.list_nodes("LLMCall")
    assert_failed_row(row)
    assert not graph.list_nodes("CommandAudit")


@pytest.mark.parametrize("capability", ["explain", "interpret"])
def test_s265_c6_error_text_and_type_reach_no_graph_property(capability: str) -> None:
    """OPR-FAIL-01 / OPR-NEV-06 / OPR-SEC-02: reason appears only in the reply/fault."""

    class ObservedGraph(InMemoryGraphStore):
        def __init__(self) -> None:
            super().__init__()
            self.labels: set[str] = set()

        def merge_node(
            self, label: str, key: str, props: Props, *, schema_version: int = 1
        ) -> Node:
            self.labels.add(label)
            return super().merge_node(label, key, props, schema_version=schema_version)

    marker = "private-request-marker"
    graph = ObservedGraph()
    agent, _graph, _bus, sink = build_agent(RequestFailure(RuntimeError(marker)), graph)
    if capability == "explain":
        summary = agent._explain(ExplainRequest(subject="question")).summary
    else:
        summary = agent._interpret(command()).message.summary
    assert marker in summary
    assert len(sink.faults) == 1
    assert sink.faults[0].message == marker
    for label in graph.labels:
        for node in graph.list_nodes(label):
            assert marker not in repr(node.props)
            assert "RuntimeError" not in repr(node.props)
    (audit,) = graph.list_nodes("CommandAudit")
    assert set(audit.props) == {
        "correlation_id",
        "actor",
        "channel",
        "text",
        "outcome",
        "created_at",
    }
    assert_audit(graph, "explain" if capability == "explain" else "refused")


@pytest.mark.parametrize("raw", ["not json at all", "[1, 2]", ""])
def test_s265_c7_malformed_json_is_a_fault_free_audited_refusal(raw: str) -> None:
    """OPR-FAIL-01 / OPR-OUT-05: a malformed model reply is refused without a fault."""
    agent, graph, _bus, sink = build_agent(CompletionStub(response=raw))
    result = agent._interpret(command())
    assert result.outcome == "refused"
    assert result.intent is None
    assert result.message.summary
    assert not sink.faults
    (audit,) = graph.list_nodes("CommandAudit")
    assert audit.props["outcome"] == "refused"
    assert not graph.list_nodes("Intent")
