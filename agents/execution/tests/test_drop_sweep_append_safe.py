"""Append-safe drop-sweep regressions for S151.

Agent: execution
Role: prove historical broker-status evidence does not poison stale-order drops.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import agents.execution.drop_sweep as drop_sweep
from agents.execution.tests.broker_stop_helpers import TrackingBroker
from agents.execution.tests.drop_sweep_helpers import broker_order, seed_fill_lineage
from kernel import CollectingFaultSink, GraphFaultSink, InMemoryGraphStore

if TYPE_CHECKING:
    from agents.execution.broker import BrokerFill


def test_2026_07_30_collision_records_drop_without_status_rewrite() -> None:
    """EXEC-STA-03 / EXEC-OBS-02: 2026-07-30 rejected/canceled collision heals."""
    graph = InMemoryGraphStore()
    key = "old-run:ABT:buy"
    seed_fill_lineage(graph, "old-run", key, "ABT")
    graph.merge_node("Fill", key, {"broker_status": "rejected"})
    broker = TrackingBroker(
        broker_fills=(broker_order(key, "ABT", status="rejected", reason="canceled"),)
    )
    sink = GraphFaultSink(graph, CollectingFaultSink())

    dropped = drop_sweep.sweep_unfilled_orders(graph, broker, sink, run_id="new-run")

    fill = graph.get_node("Fill", key)
    assert dropped == 1
    assert fill is not None
    assert fill.props["broker_status"] == "rejected"
    assert fill.props["drop_reason"] == "unfilled at session end"
    status = graph.list_nodes("BrokerOrderStatus")[0]
    assert status.props["status"] == "canceled"


def test_never_reconciled_drop_does_not_create_broker_status() -> None:
    """EXEC-STA-03 / EXEC-OBS-02: fresh drops use drop evidence, not status props."""
    graph = InMemoryGraphStore()
    key = "old-run:BAC:buy"
    seed_fill_lineage(graph, "old-run", key, "BAC")
    broker = TrackingBroker(broker_fills=(broker_order(key, "BAC"),))

    dropped = drop_sweep.sweep_unfilled_orders(
        graph, broker, CollectingFaultSink(), run_id="new-run"
    )

    fill = graph.get_node("Fill", key)
    assert dropped == 1
    assert fill is not None
    assert "broker_status" not in fill.props
    assert fill.props["drop_reason"] == "unfilled at session end"


def test_append_only_store_still_rejects_direct_status_overwrite() -> None:
    """EXEC-STA-03 / DEP-POSTGRES-03: caller fixed, append-only guard intact."""
    graph = InMemoryGraphStore()
    graph.merge_node("Fill", "fill", {"broker_status": "rejected"})

    with pytest.raises(
        ValueError, match="property 'broker_status' cannot be overwritten"
    ):
        graph.merge_node("Fill", "fill", {"broker_status": "canceled"})


def test_ten_legacy_reconciled_fills_sweep_cleanly() -> None:
    """EXEC-FAIL-01 / EXEC-OBS-02: ten legacy canceled fills do not poison sweep."""
    graph = InMemoryGraphStore()
    orders = []
    for index in range(10):
        ticker = f"L{index}"
        key = f"old-run:{ticker}:buy"
        seed_fill_lineage(graph, "old-run", key, ticker)
        graph.merge_node("Fill", key, {"broker_status": "rejected"})
        orders.append(broker_order(key, ticker, status="rejected", reason="canceled"))
    broker = TrackingBroker(broker_fills=tuple(orders))
    sink = GraphFaultSink(graph, CollectingFaultSink())

    dropped = drop_sweep.sweep_unfilled_orders(graph, broker, sink, run_id="new-run")

    assert dropped == 10
    assert len(graph.list_nodes("BrokerOrderStatus")) == 10
    assert all(
        fill.props.get("drop_reason") == "unfilled at session end"
        for fill in graph.list_nodes("Fill")
    )


def test_broker_read_failure_records_fault_and_returns_empty() -> None:
    """EXEC-FAIL-02 / EXEC-OBS-02: broker.fills failure degrades without raising."""

    class FillsFailBroker(TrackingBroker):
        def fills(self) -> tuple[BrokerFill, ...]:
            raise RuntimeError("broker fills unavailable")

    graph = InMemoryGraphStore()
    sink = GraphFaultSink(graph, CollectingFaultSink())

    dropped = drop_sweep.sweep_unfilled_orders(
        graph, FillsFailBroker(), sink, run_id="new-run"
    )

    assert dropped == 0
    faults = graph.list_nodes("Fault")
    assert len(faults) == 1
    assert "broker fills unavailable" in faults[0].props["message"]


def test_rollup_failure_is_contained_after_drops_are_recorded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """EXEC-FAIL-03 / EXEC-OBS-02: roll-up failure cannot undo recorded drops."""
    graph = InMemoryGraphStore()
    key = "old-run:USB:buy"
    seed_fill_lineage(graph, "old-run", key, "USB")
    broker = TrackingBroker(broker_fills=(broker_order(key, "USB"),))
    sink = GraphFaultSink(graph, CollectingFaultSink())

    def fail_rollup(*_: object) -> None:
        raise RuntimeError("rollup poisoned")

    monkeypatch.setattr(drop_sweep, "mark_execution_runs", fail_rollup)

    dropped = drop_sweep.sweep_unfilled_orders(graph, broker, sink, run_id="new-run")

    fill = graph.get_node("Fill", key)
    assert dropped == 1
    assert fill is not None
    assert fill.props["drop_reason"] == "unfilled at session end"
    assert any(
        "rollup poisoned" in fault.props["message"]
        for fault in graph.list_nodes("Fault")
    )
