"""Surface query tests.

Agent: surfaces
Role: verify graph projections for runs, positions, and health.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from kernel import GraphStore, InMemoryGraphStore
from surfaces.queries import (
    open_positions,
    positions_for_run,
    recent_runs,
    run_detail,
    system_health,
)
from surfaces.queries._graph import nodes_by_label
from surfaces.tests.performance_fixtures import seed_run

if TYPE_CHECKING:
    from kernel import Node


def test_recent_runs_handles_empty_and_non_local_graphs() -> None:
    graph = InMemoryGraphStore()
    assert recent_runs(graph) == ()
    assert run_detail(graph, "missing") is None
    assert nodes_by_label(cast("GraphStore", _ListOnlyGraph()), "Message") == ()


def test_system_health_counts_faults_flags_and_last_run() -> None:
    graph = InMemoryGraphStore()
    assert system_health(graph).healthy is True
    graph.merge_node("Fault", "fault:open", {"status": "pending"})
    graph.merge_node("Fault", "fault:done", {"status": "resolved"})
    graph.merge_node("Flag", "flag:warn", {"subject_ref": "warn", "severity": "warn"})
    graph.merge_node(
        "Flag", "flag:critical", {"subject_ref": "critical", "severity": "critical"}
    )
    graph.merge_node(
        "FlagResolution",
        "resolution:flag:critical:critical",
        {"subject_ref": "critical", "severity": "critical"},
    )
    seed_run(graph, "old", requested_at="2026-09-23T22:30:00+00:00")
    seed_run(graph, "new", requested_at="2026-09-24T22:30:00+00:00")

    health = system_health(graph)

    assert health.healthy is False
    assert health.open_faults == 1
    assert health.pending_flags == 1
    assert health.last_run_id == "new"


def test_open_positions_and_positions_for_run_project_broker_close_state() -> None:
    """ADR-0015 s1: surfaces keep decided positions visible until broker closure."""
    graph = InMemoryGraphStore()
    open_position = _position(graph, "run-a:AAPL", "run-a", "AAPL")
    decided_by_edge = _position(graph, "run-a:MSFT", "run-a", "MSFT")
    non_close_edge = _position(graph, "run-a:TSLA", "run-a", "TSLA")
    _position(graph, "run-b:NVDA", "run-b", "NVDA", broker_absent=True)
    close = graph.merge_node(
        "CloseDecision",
        "monitor:run-a:MSFT:close",
        {"decision": "close", "trigger": "stop"},
    )
    graph.add_edge(close, decided_by_edge, "CLOSES")
    other = graph.merge_node("OtherDecision", "monitor:run-a:TSLA:note", {})
    graph.add_edge(other, non_close_edge, "CLOSES")

    open_views = open_positions(graph)
    run_views = positions_for_run(graph, "run-a")

    assert [view.position_id for view in open_views] == [
        open_position.key,
        decided_by_edge.key,
        non_close_edge.key,
    ]
    assert [view.position_id for view in run_views] == [
        "run-a:AAPL",
        "run-a:MSFT",
        "run-a:TSLA",
    ]
    assert run_views[1].status == "open"
    assert run_views[1].close_trigger == "stop"


def _position(
    graph: InMemoryGraphStore,
    key: str,
    run_id: str,
    ticker: str,
    *,
    status: str = "open",
    broker_absent: bool = False,
) -> Node:
    return graph.merge_node(
        "Position",
        key,
        {
            "run_id": run_id,
            "ticker": ticker,
            "quantity": 2,
            "opened_price_cents": 10100,
            "status": status,
            "broker_absent": broker_absent,
        },
    )


class _ListOnlyGraph:
    def list_nodes(self, label: str) -> tuple[Node, ...]:
        del label
        return ()
