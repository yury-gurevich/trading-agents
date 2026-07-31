"""Position-sync containment for drop-sweep failures.

Agent: execution
Role: prove stale-order cleanup cannot keep RunRequest sync pending.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import agents.execution.poll as poll
from agents.execution.broker import BrokerPosition
from agents.execution.poll import find_pending_position_sync, sync_run_request
from agents.execution.tests.broker_stop_helpers import TrackingBroker
from agents.execution.tests.drop_sweep_helpers import broker_order, seed_fill_lineage
from agents.execution.tests.helpers import PositionBroker
from contracts.position_sync import (
    RUN_REQUEST_LABEL,
    linked_snapshot,
    run_request_key,
)
from kernel import CollectingFaultSink, GraphFaultSink, InMemoryGraphStore

if TYPE_CHECKING:
    import pytest

    from kernel import Node


def test_sweep_failure_never_costs_the_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """EXEC-FAIL-02 / EXEC-OBS-02: planted sweep failure still links snapshot."""
    graph = InMemoryGraphStore()
    request = _run_request(graph, "sweep-poisoned")
    broker = PositionBroker((BrokerPosition("AAPL", 3, 10000, 30000),))
    sink = GraphFaultSink(graph, CollectingFaultSink())

    def poison_sweep(*_: object, **__: object) -> int:
        raise RuntimeError("sweep poisoned")

    monkeypatch.setattr(poll, "sweep_unfilled_orders", poison_sweep)

    sync_run_request(request, graph=graph, broker=broker, sink=sink)

    snapshot = linked_snapshot(graph, request)
    assert snapshot is not None
    assert snapshot.props["status"] == "fresh"
    faults = graph.list_nodes("Fault")
    assert len(faults) == 1
    assert "sweep poisoned" in faults[0].props["message"]
    assert find_pending_position_sync(graph) == []


def test_legacy_drop_collision_through_poll_completes_position_sync() -> None:
    """EXEC-STA-03 / EXEC-IDM-02: poisoned sweep shape stops being pending."""
    graph = InMemoryGraphStore()
    request = _run_request(graph, "legacy-collision")
    key = "old-run:ABT:buy"
    seed_fill_lineage(graph, "old-run", key, "ABT")
    graph.merge_node("Fill", key, {"broker_status": "rejected"})
    broker = TrackingBroker(
        broker_fills=(broker_order(key, "ABT", status="rejected", reason="canceled"),),
        broker_positions=(BrokerPosition("ABT", 96, 10437, 1000000),),
    )
    sink = GraphFaultSink(graph, CollectingFaultSink())

    sync_run_request(request, graph=graph, broker=broker, sink=sink)

    fill = graph.get_node("Fill", key)
    assert fill is not None
    assert fill.props["broker_status"] == "rejected"
    assert fill.props["drop_reason"] == "unfilled at session end"
    assert linked_snapshot(graph, request) is not None
    assert find_pending_position_sync(graph) == []


def _run_request(graph: InMemoryGraphStore, run_id: str) -> Node:
    return graph.merge_node(
        RUN_REQUEST_LABEL,
        run_request_key(run_id),
        {"run_id": run_id, "tickers": ("AAPL",)},
    )
