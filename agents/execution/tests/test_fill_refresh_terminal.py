"""Execution terminal-fill refresh tests.

Agent: execution
Role: prove settled fills stop refreshing broker order-status evidence.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from agents.execution.broker import BrokerFill
from agents.execution.reconciliation_store import refresh_pending_fills
from contracts.common import Money
from kernel import CollectingFaultSink, InMemoryGraphStore, Node


def test_filled_broker_status_is_not_reselected_for_order_status_writes() -> None:
    """EXEC-STA-05 / EXEC-IDM-01: terminal filled refresh is a no-op."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    key = _pending_fill(graph, "AAPL", broker_status="filled")

    refresh_pending_fills(graph, (_broker_fill(key, "AAPL", "buy", 1, "filled"),), sink)

    assert graph.list_nodes("BrokerOrderStatus") == ()
    assert _refresh_edge_count(graph, key) == 0


def test_rejected_broker_status_is_not_reselected_for_order_status_writes() -> None:
    """EXEC-STA-05 / EXEC-IDM-01: terminal rejected refresh is a no-op."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    key = _pending_fill(graph, "AAPL", broker_status="rejected")

    refresh_pending_fills(
        graph, (_broker_fill(key, "AAPL", "buy", 1, "rejected"),), sink
    )

    assert graph.list_nodes("BrokerOrderStatus") == ()
    assert _refresh_edge_count(graph, key) == 0


def test_partial_broker_status_still_refreshes_status_evidence() -> None:
    """EXEC-STA-05 / EXEC-OBS-01: partial fills keep observable refreshes."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    key = _pending_fill(graph, "AAPL", broker_status="partial")

    refresh_pending_fills(
        graph, (_broker_fill(key, "AAPL", "buy", 1, "partial"),), sink
    )

    assert len(graph.list_nodes("BrokerOrderStatus")) == 1
    assert _refresh_edge_count(graph, key) == 1


def test_pending_fill_without_broker_match_writes_no_status_evidence() -> None:
    """EXEC-OBS-01 / EXEC-IDM-01: absent broker fill refresh is a no-op."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    key = _pending_fill(graph, "AAPL")

    refresh_pending_fills(graph, (), sink)

    assert graph.list_nodes("BrokerOrderStatus") == ()
    assert _refresh_edge_count(graph, key) == 0


def test_first_refresh_without_broker_status_still_records_terminal_evidence() -> None:
    """EXEC-STA-03 / EXEC-OBS-01: first terminal broker fact is still written."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    key = _pending_fill(graph, "AAPL")

    refresh_pending_fills(graph, (_broker_fill(key, "AAPL", "buy", 1, "filled"),), sink)

    fill = _fill(graph, key)
    assert fill.props["broker_status"] == "filled"
    assert len(graph.list_nodes("BrokerOrderStatus")) == 1
    assert _refresh_edge_count(graph, key) == 1


def test_terminal_fill_refresh_is_idempotent_across_five_passes() -> None:
    """EXEC-IDM-01 / EXEC-STA-03: settled-fill refresh converges at N passes."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    key = _pending_fill(graph, "AAPL")
    fills = (_broker_fill(key, "AAPL", "buy", 1, "filled"),)

    for _ in range(5):
        refresh_pending_fills(graph, fills, sink)

    assert len(graph.list_nodes("BrokerOrderStatus")) == 1
    assert _refresh_edge_count(graph, key) == 1


def _pending_fill(
    graph: InMemoryGraphStore,
    ticker: str,
    *,
    broker_status: str | None = None,
) -> str:
    key = f"run:{ticker}:buy"
    props: dict[str, object] = {
        "ticker": ticker,
        "side": "buy",
        "quantity": 1,
        "price_cents": 10000,
        "price_currency": "USD",
        "broker_order_id": f"paper:{key}",
        "status": "pending",
        "reason": None,
    }
    if broker_status is not None:
        props["broker_status"] = broker_status
    graph.merge_node("Fill", key, props)
    return key


def _broker_fill(
    key: str,
    ticker: str,
    side: Literal["buy", "sell"],
    quantity: int,
    status: Literal["filled", "partial", "rejected", "pending"],
) -> BrokerFill:
    return BrokerFill(
        idempotency_key=key,
        ticker=ticker,
        side=side,
        quantity=quantity,
        price=Money(amount=Decimal("100.00")),
        broker_order_id=f"paper:{key}",
        status=status,
    )


def _fill(graph: InMemoryGraphStore, key: str) -> Node:
    fill = graph.get_node("Fill", key)
    assert fill is not None
    return fill


def _refresh_edge_count(graph: InMemoryGraphStore, key: str) -> int:
    fill = _fill(graph, key)
    edges = graph.ancestors(fill, max_depth=1, edge_types={"REFRESHES"})
    return len(tuple(edges))
