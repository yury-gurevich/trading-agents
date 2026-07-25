"""Broker-stop contract read-model tests.

Agent: contracts
Role: keep BrokerStopOrder cross-agent accessors stable.
External I/O: none.
"""

from __future__ import annotations

from contracts.broker_stops import (
    active_broker_stop_orders,
    active_broker_stop_refs,
    broker_stop_order_key,
    broker_stop_orders,
)
from kernel import InMemoryGraphStore


def test_active_broker_stop_refs_exclude_cancelled_orders() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node(
        "BrokerStopOrder",
        "stop:old:AAPL",
        {
            "ticker": "AAPL",
            "position_ref": "old-ref",
            "stop_price_cents": 9500,
            "broker_order_id": "broker-old",
            "placed_at": "2026-07-25T00:00:00+00:00",
            "cancelled_at": "2026-07-25T00:01:00+00:00",
        },
    )
    graph.merge_node(
        "BrokerStopOrder",
        "stop:live:MSFT",
        {
            "ticker": "MSFT",
            "position_ref": "live-ref",
            "stop_price_cents": 10100,
            "broker_order_id": "broker-live",
            "placed_at": "2026-07-25T00:00:00+00:00",
        },
    )

    assert broker_stop_order_key("live-ref", "MSFT") == "stop:live-ref:MSFT"
    assert active_broker_stop_refs(graph) == frozenset({"live-ref"})
    assert [order.key for order in active_broker_stop_orders(graph)] == [
        "stop:live:MSFT"
    ]
    assert [order.cancelled_at for order in broker_stop_orders(graph)] == [
        None,
        "2026-07-25T00:01:00+00:00",
    ]
