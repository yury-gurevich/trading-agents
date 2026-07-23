"""GraphFaultSink tests — faults must outlive the process that raised them.

Agent: kernel
Role: verify fault persistence, forwarding, and append-on-recurrence keying.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime

from kernel import CollectingFaultSink, GraphFaultSink, InMemoryGraphStore
from kernel.errors import AgentFault
from surfaces.queries.faults import open_faults


def _fault(message: str = "execution error", **overrides: object) -> AgentFault:
    props: dict[str, object] = {
        "source_agent": "monitor",
        "source_module": "agents.monitor.execution_client",
        "capability": "check_positions",
        "error_type": "RuntimeError",
        "message": message,
    }
    props.update(overrides)
    return AgentFault.model_validate(props)


def test_fault_is_persisted_and_forwarded() -> None:
    """A submitted fault reaches the graph and the wrapped sink."""
    graph = InMemoryGraphStore()
    inner = CollectingFaultSink()
    sink = GraphFaultSink(graph, inner)

    sink.submit(_fault())

    nodes = graph.list_nodes("Fault")
    assert len(nodes) == 1
    assert nodes[0].props["source_agent"] == "monitor"
    assert nodes[0].props["message"] == "execution error"
    assert nodes[0].props["status"] == "pending"
    assert [item.message for item in inner.faults] == ["execution error"]


def test_recurring_fault_appends_rather_than_overwrites() -> None:
    """The same failure on two runs is two nodes — recurrence is itself the signal."""
    graph = InMemoryGraphStore()
    sink = GraphFaultSink(graph, CollectingFaultSink())

    sink.submit(_fault(occurred_at=datetime(2026, 7, 20, 22, 41, tzinfo=UTC)))
    sink.submit(_fault(occurred_at=datetime(2026, 7, 21, 22, 41, tzinfo=UTC)))

    assert len(graph.list_nodes("Fault")) == 2


def test_persisted_fault_reaches_the_operator_surface() -> None:
    """The incident view is empty until something actually writes a Fault node."""
    graph = InMemoryGraphStore()
    sink = GraphFaultSink(graph, CollectingFaultSink())
    assert open_faults(graph) == ()

    sink.submit(_fault("close dispatch failed"))

    views = open_faults(graph)
    assert [view.source_agent for view in views] == ["monitor"]
    assert [view.message for view in views] == ["close dispatch failed"]
