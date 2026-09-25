"""A replaced stop is dead in the one liveness question (S230, EXEC-OBS-05).

Agent: contracts
Role: prove `replaced` is terminal and a `replaced_at` marker ends a stop fact.
External I/O: none.

Before S230 `replaced` was absent from the terminal set, so an order the broker
had superseded by an in-place replace would have read live forever.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from contracts.broker_lifecycle import (
    is_live_broker_stop_fact,
    is_live_broker_stop_order,
)
from contracts.broker_stops import (
    BROKER_STOP_ORDER_LABEL,
    active_broker_stop_orders,
    free_broker_stop_order_key,
)
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from kernel import Node


@dataclass(frozen=True)
class _Order:
    idempotency_key: str
    broker_order_id: str
    order_type: str | None
    status: str
    reason: str | None = None


def test_a_replaced_order_is_not_live() -> None:
    """EXEC-OBS-05: A10 - `replaced` is terminal where liveness is asked."""
    replaced = _Order("stop:ref:USB", "old-id", "stop", "replaced")
    resting = _Order("stop:ref:USB#1", "new-id", "stop", "new")

    assert is_live_broker_stop_order(replaced) is False
    assert is_live_broker_stop_order(resting) is True


def test_a_replaced_at_marker_ends_the_fact_without_deleting_it() -> None:
    """EXEC-OBS-03 / EXEC-OBS-05: A10 - the marker ends liveness; the fact remains."""
    graph = InMemoryGraphStore()
    old = _stop(graph, "stop:ref:USB", "old-id")
    graph.merge_node(BROKER_STOP_ORDER_LABEL, old.key, {"replaced_at": "2026-09-25"})
    new = _stop(graph, "stop:ref:USB#1", "new-id")

    marked = graph.get_node(BROKER_STOP_ORDER_LABEL, old.key)
    assert marked is not None
    assert is_live_broker_stop_fact(graph, marked) is False
    assert is_live_broker_stop_fact(graph, new) is True
    assert [order.key for order in active_broker_stop_orders(graph)] == [new.key]


def test_the_free_key_skips_every_existing_attempt() -> None:
    """EXEC-OBS-03: a replacement never reuses a key, live or dead."""
    graph = InMemoryGraphStore()

    assert free_broker_stop_order_key(graph, "ref", "USB") == "stop:ref:USB"
    _stop(graph, "stop:ref:USB", "old-id")
    _stop(graph, "stop:ref:USB#1", "mid-id")

    assert free_broker_stop_order_key(graph, "ref", "USB") == "stop:ref:USB#2"


def _stop(graph: InMemoryGraphStore, key: str, broker_order_id: str) -> Node:
    return graph.merge_node(
        BROKER_STOP_ORDER_LABEL,
        key,
        {
            "ticker": "USB",
            "position_ref": "ref",
            "stop_price_cents": 5747,
            "broker_order_id": broker_order_id,
            "placed_at": "2026-09-24",
        },
    )
