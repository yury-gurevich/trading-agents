"""Drop-sweep liveness tests for broker stop contracts.

Agent: execution
Role: prove broker stop drop-sweep liveness and mismatch evidence.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.drop_sweep import sweep_unfilled_orders
from agents.execution.tests.broker_stop_helpers import TrackingBroker
from agents.execution.tests.drop_sweep_helpers import broker_order
from kernel import CollectingFaultSink, InMemoryGraphStore


def test_sweep_raises_no_mismatch_for_dead_stop_order() -> None:
    """EXEC-OUT-07 / EXEC-OBS-05: dead broker stops match dead graph stops."""
    graph = InMemoryGraphStore()
    key = "stop:ref-dead:WFC"
    graph.merge_node(
        "BrokerStopOrder",
        key,
        {
            "ticker": "WFC",
            "position_ref": "ref-dead",
            "stop_price_cents": 9500,
            "broker_order_id": "broker:dead-stop",
            "placed_at": "2026-08-01T00:00:00+00:00",
            "cancelled_at": "2026-08-02T00:00:00+00:00",
        },
    )
    broker = TrackingBroker(
        broker_fills=(
            broker_order(
                key,
                "WFC",
                status="rejected",
                reason="canceled",
                order_type="stop",
            ),
        )
    )
    sink = CollectingFaultSink()

    dropped = sweep_unfilled_orders(graph, broker, sink, run_id="new-run")

    assert dropped == 0
    assert broker.cancelled == []
    assert sink.faults == []


def test_live_stop_mismatch_fault_carries_context() -> None:
    """EXEC-OBS-05: stop identity mismatch is structured evidence."""
    graph = InMemoryGraphStore()
    order = broker_order(
        "stop:missing:AMD",
        "AMD",
        order_type="stop",
        status="pending",
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
        "idempotency_key": "stop:missing:AMD",
        "broker_order_id": "broker:stop:missing:AMD",
        "order_type": "stop",
        "broker_status": "pending",
        "broker_stop": True,
        "graph_stop": False,
    }
