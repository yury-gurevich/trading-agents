"""Synthetic payload cases for the six remaining finders (S252, DL-261).

Agent: tooling
Role: seed done, pending and not-ready work, including snapshots with no request.
External I/O: none (in-memory graph).
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from tests.poll_payload_support import NOW, PollCase, seed_chain

from agents.execution.tests.helpers import order, order_set
from agents.provider.tests.barrier_history_helpers import analyst_run, rec

if TYPE_CHECKING:
    from kernel import GraphStore


def seed_forecast(graph: GraphStore) -> None:
    """Current runs c/a are ready; b is done and waiting has no history yet."""
    seed_chain(graph, "AnalystRun", "FORECAST_BY", "ForecasterRun")
    for key in ("c", "b", "a"):
        graph.merge_node("AnalystRun", key, {"created_at": NOW.isoformat()})
    analyst_run(graph, rec("AAPL", "buy"), key="waiting")
    graph.merge_node("AnalystRun", "waiting", {"created_at": NOW.isoformat()})


def seed_settlement(graph: GraphStore) -> None:
    """Current runs c/a have no pass; b has already been settled."""
    seed_chain(graph, "AnalystRun", "BARRIER_SETTLEMENT_BY", "BarrierSettlementPass")
    for key in ("c", "b", "a"):
        graph.merge_node("AnalystRun", key, {"created_at": NOW.isoformat()})
    graph.merge_node(
        "AnalystRun", "stale", {"created_at": (NOW - timedelta(days=2)).isoformat()}
    )


def seed_forecaster_backlog(graph: GraphStore) -> None:
    """71 unmarked stale AnalystRuns and one current run, ready without history."""
    for index in range(71):
        graph.merge_node(
            "AnalystRun",
            f"stale-{index:02d}",
            {"created_at": (NOW - timedelta(days=2)).isoformat()},
        )
    graph.merge_node("AnalystRun", "current", {"created_at": NOW.isoformat()})


def seed_deliberator(graph: GraphStore) -> None:
    """Order-carrying c/a are pending; b is done; no-orders is fetched only."""
    seed_chain(graph, "PMRun", "DELIBERATED_BY", "DeliberationRun")
    for key in ("c", "b", "a"):
        graph.merge_node("PMRun", key, {"order_intent_set": {}})
    graph.merge_node("PMRun", "no-orders", {})


def seed_execution(graph: GraphStore) -> None:
    """c/a are ready, b is executed, and a fresh buy waits for deliberation."""
    seed_chain(graph, "PMRun", "EXECUTED_BY", "ExecutionRun")
    graph.merge_node(
        "PMRun",
        "waiting",
        {
            "created_at": NOW.isoformat(),
            "order_intent_set": order_set(order("AAPL")).model_dump(mode="json"),
        },
    )


def seed_execution_sync(graph: GraphStore) -> None:
    """RunRequests c/a have no snapshot; b has the completed REFRESHES edge."""
    seed_chain(graph, "RunRequest", "REFRESHES", "BrokerPositionSnapshot")


def seed_monitor_sync(graph: GraphStore) -> None:
    """Request-order c/a/half snapshots, b done, awaiting unwritten, 106 orphans."""
    requests = {
        key: graph.merge_node("RunRequest", f"run-request:{key}", {"run_id": key})
        for key in ("c", "b", "a", "awaiting", "half")
    }
    for key in ("b", "a", "c", "half"):
        snapshot = graph.merge_node(
            "BrokerPositionSnapshot",
            f"snapshot:{key}",
            {"run_id": key, "status": "stale", "holdings": ()},
        )
        graph.add_edge(requests[key], snapshot, "REFRESHES")
        if key in ("b", "half"):
            marker = graph.merge_node(
                "MonitorRun",
                f"position-sync:{key}",
                {"phase": "sync", "position_book_status": "stale"},
            )
            graph.add_edge(snapshot, marker, "MONITORED_BY")
            if key == "b":
                graph.add_edge(requests[key], marker, "POSITION_SYNCED_BY")
    for index in range(106):
        graph.merge_node(
            "BrokerPositionSnapshot",
            f"snapshot:pm-{index:03d}",
            {"run_id": f"pm-{index:03d}", "status": "stale", "holdings": ()},
        )


REMAINING_CASES = (
    PollCase(
        "forecaster",
        "AnalystRun",
        "FORECAST_BY",
        seed_forecast,
        ("c", "a", "waiting"),
        ("c", "a"),
    ),
    PollCase(
        "settlement",
        "AnalystRun",
        "BARRIER_SETTLEMENT_BY",
        seed_settlement,
        ("c", "a"),
        ("c", "a"),
    ),
    PollCase(
        "deliberator",
        "PMRun",
        "DELIBERATED_BY",
        seed_deliberator,
        ("c", "a", "no-orders"),
        ("c", "a"),
    ),
    PollCase(
        "execution",
        "PMRun",
        "EXECUTED_BY",
        seed_execution,
        ("c", "a", "waiting"),
        ("c", "a"),
    ),
    PollCase(
        "execution_sync",
        "RunRequest",
        "REFRESHES",
        seed_execution_sync,
        ("c", "a"),
        ("c", "a"),
    ),
    PollCase(
        "monitor_sync",
        "RunRequest",
        "POSITION_SYNCED_BY",
        seed_monitor_sync,
        ("run-request:c", "run-request:a", "run-request:awaiting", "run-request:half"),
        ("snapshot:c", "snapshot:a", "snapshot:half"),
    ),
)
