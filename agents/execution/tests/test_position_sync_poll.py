"""Execution head-of-run position-sync poll tests.

Agent: execution
Role: prove RunRequest-driven broker snapshots are idempotent and contained.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.execution.broker import BrokerPosition
from agents.execution.poll import find_pending_position_sync, sync_run_request
from agents.execution.tests.helpers import (
    FailFirstBroker,
    FailingBroker,
    PositionBroker,
)
from contracts.position_sync import (
    RUN_REQUEST_LABEL,
    SNAPSHOT_LABEL,
    SNAPSHOT_REFRESH_EDGE,
    linked_snapshot,
    run_request_key,
)
from kernel import CollectingFaultSink, GraphFaultSink, InMemoryGraphStore
from kernel.work_loop import run_once

if TYPE_CHECKING:
    from kernel import Node


def test_sync_work_source_finds_only_unsynced_runs() -> None:
    """EXEC-TRG-01 / EXEC-IDN-01: planted synced run is not pending again."""
    graph = InMemoryGraphStore()
    first = _run_request(graph, "needs-sync")
    second = _run_request(graph, "already-synced")
    snapshot = graph.merge_node(
        SNAPSHOT_LABEL,
        "broker-position-snapshot:already-synced",
        {"run_id": "already-synced", "status": "fresh", "holdings": ()},
    )
    graph.add_edge(second, snapshot, SNAPSHOT_REFRESH_EDGE)

    assert find_pending_position_sync(graph) == [first]


def test_sync_writes_fresh_snapshot_from_broker_truth() -> None:
    """EXEC-IDN-01 / EXEC-OBS-02: broker holdings become a fresh snapshot."""
    graph = InMemoryGraphStore()
    request = _run_request(graph, "fresh-run")
    broker = PositionBroker(
        (
            BrokerPosition("AAPL", 3, 10000, 30000),
            BrokerPosition("MSFT", 5, 20000, 100000),
            BrokerPosition("NVDA", 2, 15000, 30000),
        )
    )

    sync_run_request(request, graph=graph, broker=broker)

    snapshot = linked_snapshot(graph, request)
    assert snapshot is not None
    assert snapshot.props["run_id"] == "fresh-run"
    assert snapshot.props["status"] == "fresh"
    assert snapshot.props["holding_count"] == 3
    assert snapshot.props["holdings"] == (
        {
            "ticker": "AAPL",
            "quantity": 3,
            "avg_entry_cents": 10000,
            "market_value_cents": 30000,
        },
        {
            "ticker": "MSFT",
            "quantity": 5,
            "avg_entry_cents": 20000,
            "market_value_cents": 100000,
        },
        {
            "ticker": "NVDA",
            "quantity": 2,
            "avg_entry_cents": 15000,
            "market_value_cents": 30000,
        },
    )


def test_sync_broker_failure_degrades_without_raising() -> None:
    """EXEC-FAIL-02 / EXEC-OBS-02: broker failure writes stale snapshot and Fault."""
    graph = InMemoryGraphStore()
    request = _run_request(graph, "stale-run")
    inner = CollectingFaultSink()
    sink = GraphFaultSink(graph, inner)

    sync_run_request(request, graph=graph, broker=FailingBroker(), sink=sink)

    snapshot = linked_snapshot(graph, request)
    assert snapshot is not None
    assert snapshot.props["status"] == "stale"
    assert snapshot.props["stale_reason"]
    assert len(graph.list_nodes("Fault")) == 1
    assert find_pending_position_sync(graph) == []


def test_sync_is_idempotent_per_run() -> None:
    """EXEC-IDM-02 / EXEC-TRG-01: second poll pass finds no duplicate snapshot."""
    graph = InMemoryGraphStore()
    _run_request(graph, "one-pass")
    broker = PositionBroker((BrokerPosition("AAPL", 3, 10000, 30000),))

    first = run_once(
        lambda: find_pending_position_sync(graph),
        lambda node: sync_run_request(node, graph=graph, broker=broker),
    )
    second = run_once(
        lambda: find_pending_position_sync(graph),
        lambda node: sync_run_request(node, graph=graph, broker=broker),
    )

    assert (first, second) == (1, 0)
    assert len(graph.list_nodes(SNAPSHOT_LABEL)) == 1


def test_sync_failure_for_one_run_does_not_stop_next_run() -> None:
    """EXEC-FAIL-02 / EXEC-OBS-02: planted first failure does not stop next sync."""
    graph = InMemoryGraphStore()
    first = _run_request(graph, "poisoned")
    second = _run_request(graph, "healthy")
    inner = CollectingFaultSink()
    sink = GraphFaultSink(graph, inner)
    broker = FailFirstBroker()

    processed = run_once(
        lambda: find_pending_position_sync(graph),
        lambda node: sync_run_request(node, graph=graph, broker=broker, sink=sink),
    )

    first_snapshot = linked_snapshot(graph, first)
    second_snapshot = linked_snapshot(graph, second)
    assert processed == 2
    assert first_snapshot is not None
    assert second_snapshot is not None
    assert first_snapshot.props["status"] == "stale"
    assert second_snapshot.props["status"] == "fresh"
    assert len(graph.list_nodes("Fault")) == 1


def _run_request(graph: InMemoryGraphStore, run_id: str) -> Node:
    return graph.merge_node(
        RUN_REQUEST_LABEL,
        run_request_key(run_id),
        {"run_id": run_id, "tickers": ("AAPL",)},
    )
