"""GraphFaultSink tests — faults must outlive the process that raised them.

Agent: kernel
Role: verify fault persistence, forwarding, and append-on-recurrence keying.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from kernel import CollectingFaultSink, GraphFaultSink, InMemoryGraphStore
from kernel.errors import AgentFault
from kernel.fault_collapse import FaultCollapsePolicy
from kernel.fault_graph import FAULT_SUPPRESSION_LABEL, fault_node_key
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


def test_identical_faults_within_window_write_one_fault_node() -> None:
    """EXEC-OBS-02 / DRIFT-030: ongoing duplicate faults collapse by signature."""
    graph = InMemoryGraphStore()
    sink = GraphFaultSink(
        graph,
        CollectingFaultSink(),
        collapse_policy=FaultCollapsePolicy(collapse_window_seconds=60.0),
    )
    first = _fault(occurred_at=datetime(2026, 7, 30, 22, 30, tzinfo=UTC))

    sink.submit(first)
    for offset in range(1, 5):
        sink.submit(_fault(occurred_at=first.occurred_at + timedelta(seconds=offset)))

    assert graph.get_node("Fault", fault_node_key(first)) is not None
    assert len(graph.list_nodes("Fault")) == 1


def test_suppressed_fault_volume_is_recoverable() -> None:
    """EXEC-OBS-02 / DRIFT-030: collapsed duplicate volume stays queryable."""
    graph = InMemoryGraphStore()
    sink = GraphFaultSink(
        graph,
        CollectingFaultSink(),
        collapse_policy=FaultCollapsePolicy(collapse_window_seconds=60.0),
    )
    first = _fault(occurred_at=datetime(2026, 7, 30, 22, 30, tzinfo=UTC))

    for offset in range(5):
        sink.submit(_fault(occurred_at=first.occurred_at + timedelta(seconds=offset)))
    sink.flush()

    summaries = graph.list_nodes(FAULT_SUPPRESSION_LABEL)
    views = open_faults(graph)
    assert len(summaries) == 1
    assert summaries[0].props["first_fault_key"] == fault_node_key(first)
    assert summaries[0].props["occurrence_count"] == 5
    assert summaries[0].props["suppressed_count"] == 4
    assert views[0].occurrence_count == 5
    assert views[0].suppressed_count == 4


def test_distinct_fault_signatures_both_write() -> None:
    """EXEC-OBS-02 / DRIFT-030: collapse never swallows a distinct failure."""
    graph = InMemoryGraphStore()
    sink = GraphFaultSink(
        graph,
        CollectingFaultSink(),
        collapse_policy=FaultCollapsePolicy(collapse_window_seconds=60.0),
    )
    occurred_at = datetime(2026, 7, 30, 22, 30, tzinfo=UTC)

    sink.submit(_fault(occurred_at=occurred_at, message="first failure"))
    sink.submit(
        _fault(
            occurred_at=occurred_at + timedelta(seconds=1),
            message="second failure",
        )
    )

    assert len(graph.list_nodes("Fault")) == 2


def test_fault_recurring_after_window_still_appends() -> None:
    """EXEC-OBS-02 / DRIFT-030: recurrence across runs remains visible."""
    graph = InMemoryGraphStore()
    sink = GraphFaultSink(
        graph,
        CollectingFaultSink(),
        collapse_policy=FaultCollapsePolicy(collapse_window_seconds=60.0),
    )
    first = _fault(occurred_at=datetime(2026, 7, 30, 22, 30, tzinfo=UTC))
    repeated = _fault(occurred_at=first.occurred_at + timedelta(seconds=1))
    next_run = _fault(occurred_at=first.occurred_at + timedelta(hours=24))

    sink.submit(first)
    sink.submit(repeated)
    sink.submit(next_run)

    assert len(graph.list_nodes("Fault")) == 2
    assert len(graph.list_nodes(FAULT_SUPPRESSION_LABEL)) == 1


def test_persisted_fault_reaches_the_operator_surface() -> None:
    """The incident view is empty until something actually writes a Fault node."""
    graph = InMemoryGraphStore()
    sink = GraphFaultSink(graph, CollectingFaultSink())
    assert open_faults(graph) == ()

    sink.submit(_fault("close dispatch failed"))

    views = open_faults(graph)
    assert [view.source_agent for view in views] == ["monitor"]
    assert [view.message for view in views] == ["close dispatch failed"]
