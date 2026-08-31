"""Broker-stop liveness contract tests.

Agent: contracts
Role: prove BrokerStopOrder liveness is derived from broker lifecycle evidence.
External I/O: none.
"""

from __future__ import annotations

import importlib

from contracts.broker_stops import (
    BROKER_STOP_ORDER_LABEL,
    active_broker_stop_orders,
    active_broker_stop_refs,
    broker_stop_order_key,
)
from kernel import InMemoryGraphStore, Node


def test_filled_sibling_fill_makes_uncancelled_stop_inactive() -> None:
    """EXEC-OBS-03 / EXEC-OBS-05: broker truth decides stop liveness."""
    graph = InMemoryGraphStore()
    key = broker_stop_order_key("pypl-ref", "PYPL")
    _stop_fact(graph, key, "PYPL", "pypl-ref", broker_order_id="broker-pypl")
    graph.merge_node(
        "Fill",
        key,
        {
            "ticker": "PYPL",
            "side": "sell",
            "status": "pending",
            "broker_status": "filled",
            "broker_order_id": "broker-pypl",
        },
    )

    assert active_broker_stop_orders(graph) == ()
    assert active_broker_stop_refs(graph) == frozenset()


def test_stop_liveness_falls_back_to_broker_order_id() -> None:
    """EXEC-OBS-03 / EXEC-OBS-05: broker_order_id pairs stop facts to Fills."""
    graph = InMemoryGraphStore()
    key = broker_stop_order_key("pypl-ref", "PYPL")
    _stop_fact(graph, key, "PYPL", "pypl-ref", broker_order_id="broker-pypl")
    graph.merge_node(
        "Fill",
        "different-fill-key",
        {
            "ticker": "PYPL",
            "side": "sell",
            "status": "pending",
            "broker_status": "filled",
            "broker_order_id": "broker-pypl",
        },
    )

    assert active_broker_stop_orders(graph) == ()


def test_cancelled_stop_with_nonterminal_fill_stays_inactive() -> None:
    """EXEC-OBS-03 / EXEC-OBS-05: cancellation remains an audit marker."""
    graph = InMemoryGraphStore()
    key = broker_stop_order_key("old-ref", "AAPL")
    _stop_fact(
        graph,
        key,
        "AAPL",
        "old-ref",
        broker_order_id="broker-old",
        cancelled_at="2026-08-31T00:00:00+00:00",
    )
    graph.merge_node(
        "Fill",
        key,
        {
            "ticker": "AAPL",
            "side": "sell",
            "status": "pending",
            "broker_status": "pending",
            "broker_order_id": "broker-old",
            "stop_order_key": key,
        },
    )

    assert active_broker_stop_orders(graph) == ()
    assert active_broker_stop_refs(graph) == frozenset()


def test_resting_stop_fill_keeps_stop_live() -> None:
    """EXEC-OBS-03 / EXEC-OBS-05: resting protective stops remain live."""
    graph = InMemoryGraphStore()
    key = broker_stop_order_key("held-ref", "MSFT")
    _stop_fact(graph, key, "MSFT", "held-ref", broker_order_id="broker-msft")
    graph.merge_node(
        "Fill",
        key,
        {
            "ticker": "MSFT",
            "side": "sell",
            "status": "pending",
            "broker_order_id": "broker-msft",
            "stop_order_key": key,
        },
    )

    assert [order.key for order in active_broker_stop_orders(graph)] == [key]
    assert active_broker_stop_refs(graph) == frozenset({"held-ref"})


def test_missing_sibling_fill_keeps_stop_live() -> None:
    """EXEC-OBS-05: absent sibling Fill never silently unprotects a position."""
    graph = InMemoryGraphStore()
    key = broker_stop_order_key("missing-fill-ref", "AMZN")
    _stop_fact(graph, key, "AMZN", "missing-fill-ref", broker_order_id="broker-amzn")

    assert [order.key for order in active_broker_stop_orders(graph)] == [key]


def test_stop_without_broker_order_id_defaults_live() -> None:
    """EXEC-OBS-05: an incomplete stop fact is never silently dead."""
    lifecycle = importlib.import_module("contracts.broker_lifecycle")
    graph = InMemoryGraphStore()
    stop = Node(
        "BrokerStopOrder",
        "stop:missing-id:AAPL",
        {
            "ticker": "AAPL",
            "position_ref": "missing-id",
            "stop_price_cents": 9500,
            "placed_at": "2026-08-31T00:00:00+00:00",
        },
    )

    assert lifecycle.sibling_fill_for_broker_stop(graph, stop) is None
    assert lifecycle.is_live_broker_stop_fact(graph, stop) is True


def _stop_fact(
    graph: InMemoryGraphStore,
    key: str,
    ticker: str,
    position_ref: str,
    *,
    broker_order_id: str,
    cancelled_at: str | None = None,
) -> None:
    props: dict[str, object] = {
        "ticker": ticker,
        "position_ref": position_ref,
        "stop_price_cents": 9500,
        "broker_order_id": broker_order_id,
        "placed_at": "2026-08-31T00:00:00+00:00",
    }
    if cancelled_at is not None:
        props["cancelled_at"] = cancelled_at
    graph.merge_node(BROKER_STOP_ORDER_LABEL, key, props)
