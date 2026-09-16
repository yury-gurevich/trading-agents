"""Drop-sweep identity tests for broker stop mismatch evidence.

Agent: execution
Role: prove stale-order stop mismatches compare identity, not liveness.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.drop_sweep import sweep_unfilled_orders
from agents.execution.tests.broker_stop_helpers import TrackingBroker
from agents.execution.tests.drop_sweep_helpers import broker_order
from kernel import CollectingFaultSink, InMemoryGraphStore


def _seed_stop(
    graph: InMemoryGraphStore,
    key: str,
    ticker: str,
    position_ref: str,
    broker_order_id: str,
) -> None:
    graph.merge_node(
        "BrokerStopOrder",
        key,
        {
            "ticker": ticker,
            "position_ref": position_ref,
            "stop_price_cents": 9500,
            "broker_order_id": broker_order_id,
            "placed_at": "2026-09-15T14:21:16+00:00",
        },
    )


def test_fired_stop_with_unrefreshed_graph_status_raises_no_mismatch() -> None:
    """EXEC-OBS-05: fired stops are not stop-identity mismatches."""
    graph = InMemoryGraphStore()
    key = "stop:amzn-ref:AMZN"
    _seed_stop(graph, key, "AMZN", "amzn-ref", f"broker:{key}")
    graph.merge_node(
        "Fill",
        key,
        {
            "ticker": "AMZN",
            "side": "sell",
            "quantity": 1,
            "status": "pending",
            "broker_order_id": f"broker:{key}",
            "stop_order_key": key,
        },
    )
    broker = TrackingBroker(
        broker_fills=(broker_order(key, "AMZN", status="filled", order_type="stop"),)
    )
    sink = CollectingFaultSink()

    dropped = sweep_unfilled_orders(graph, broker, sink, run_id="new-run")

    assert dropped == 0
    assert broker.cancelled == []
    assert sink.faults == []


def test_graph_stop_identity_mismatch_still_faults() -> None:
    """EXEC-OBS-05: graph-only stop identity mismatches stay visible."""
    graph = InMemoryGraphStore()
    order = broker_order(
        "old-run:AMZN:buy",
        "AMZN",
        order_type="limit",
        status="pending",
    )
    _seed_stop(
        graph,
        "stop:graph-only:AMZN",
        "AMZN",
        "graph-only",
        order.broker_order_id,
    )
    broker = TrackingBroker(broker_fills=(order,))
    sink = CollectingFaultSink()

    dropped = sweep_unfilled_orders(graph, broker, sink, run_id="new-run")

    assert dropped == 0
    assert broker.cancelled == []
    assert len(sink.faults) == 1
    fault = sink.faults[0]
    assert fault.error_type == "BrokerStopIdentityMismatch"
    assert fault.context == {
        "idempotency_key": "old-run:AMZN:buy",
        "broker_order_id": "broker:old-run:AMZN:buy",
        "order_type": "limit",
        "broker_status": "pending",
        "broker_stop": False,
        "graph_stop": True,
    }
