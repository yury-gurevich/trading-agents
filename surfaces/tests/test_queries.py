"""Surface query tests.

Agent: surfaces
Role: verify graph projections for runs, positions, and health.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, cast

from kernel import GraphStore, InMemoryGraphStore
from surfaces.queries import (
    open_positions,
    positions_for_run,
    recent_runs,
    run_detail,
    system_health,
)
from surfaces.queries._graph import nodes_by_label

if TYPE_CHECKING:
    from kernel import Node


def test_recent_runs_returns_newest_completed_summaries() -> None:
    graph = InMemoryGraphStore()
    _seed_run(graph, "old-run", "2026-06-10T00:00:00+00:00")
    _seed_run(graph, "new-run", "2026-06-11T00:00:00+00:00")
    graph.merge_node("Snapshot", "snapshot:new-run", {"run_id": "new-run"})
    graph.merge_node("Message", "missing-run-id", {"step": "scan"})
    graph.merge_node("Fault", "fault:ignored", {})

    runs = recent_runs(graph)

    assert [run.run_id for run in runs] == ["new-run", "old-run"]
    assert runs[0].completed is True
    assert runs[0].message_count == len(_STEPS)
    assert runs[0].snapshot_available is True
    assert [step.name for step in runs[0].steps] == list(_STEPS)
    assert recent_runs(graph, limit=1) == (runs[0],)
    assert run_detail(graph, "new-run") == runs[0]


def test_recent_runs_handles_empty_and_non_local_graphs() -> None:
    graph = InMemoryGraphStore()
    assert recent_runs(graph) == ()
    assert run_detail(graph, "missing") is None
    assert nodes_by_label(cast("GraphStore", _OddGraph()), "Message") == ()
    assert nodes_by_label(cast("GraphStore", _ObjectNodeGraph()), "Message") == ()


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
    graph.merge_node("Snapshot", "snapshot:old", {"run_id": "old", "created_at": "1"})
    graph.merge_node("Snapshot", "snapshot:new", {"run_id": "new", "created_at": "2"})

    health = system_health(graph)

    assert health.healthy is False
    assert health.open_faults == 1
    assert health.pending_flags == 1
    assert health.last_run_id == "new"


def test_open_positions_and_positions_for_run_project_close_state() -> None:
    graph = InMemoryGraphStore()
    open_position = _position(graph, "run-a:AAPL", "run-a", "AAPL")
    closed_by_edge = _position(graph, "run-a:MSFT", "run-a", "MSFT")
    non_close_edge = _position(graph, "run-a:TSLA", "run-a", "TSLA")
    _position(graph, "run-b:NVDA", "run-b", "NVDA", status="closed")
    close = graph.merge_node(
        "CloseDecision",
        "monitor:run-a:MSFT:close",
        {"decision": "close", "trigger": "stop"},
    )
    graph.add_edge(close, closed_by_edge, "CLOSES")
    other = graph.merge_node("OtherDecision", "monitor:run-a:TSLA:note", {})
    graph.add_edge(other, non_close_edge, "CLOSES")

    open_views = open_positions(graph)
    run_views = positions_for_run(graph, "run-a")

    assert [view.position_id for view in open_views] == [
        open_position.key,
        non_close_edge.key,
    ]
    assert [view.position_id for view in run_views] == [
        "run-a:AAPL",
        "run-a:MSFT",
        "run-a:TSLA",
    ]
    assert run_views[1].status == "closed"
    assert run_views[1].close_trigger == "stop"


def _seed_run(graph: InMemoryGraphStore, run_id: str, created_at: str) -> None:
    for step in _STEPS:
        graph.merge_node(
            "Message",
            f"{run_id}:{step}",
            {
                "run_id": run_id,
                "step": step,
                "status": "completed",
                "created_at": created_at,
            },
        )


def _position(
    graph: InMemoryGraphStore,
    key: str,
    run_id: str,
    ticker: str,
    *,
    status: str = "open",
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
        },
    )


_STEPS = (
    "scan",
    "analyze",
    "evaluate",
    "submit",
    "check_positions",
    "report",
    "narrative",
)


class _OddGraph:
    _nodes = object()


class _ObjectNodeGraph:
    _nodes: ClassVar[dict[str, object]] = {"bad": object()}
