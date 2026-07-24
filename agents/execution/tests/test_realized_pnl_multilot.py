"""Execution realized-PnL multi-lot tests.

Agent: execution
Role: pin fill-time PnL behavior when a position_ref spans multiple lots.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from agents.execution.broker import BrokerFill
from agents.execution.reconciliation_store import refresh_pending_fills
from contracts.common import Money
from contracts.positions import open_positions
from kernel import CollectingFaultSink, InMemoryGraphStore


def test_multi_lot_full_exit_sums_known_lots() -> None:
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    _position(graph, "a:AAPL", "AAPL", quantity=2, opened_price_cents=10000)
    _position(graph, "b:AAPL", "AAPL", quantity=3, opened_price_cents=10100)
    ref = open_positions(graph)[0].position_ref
    key = _pending_sell(graph, "AAPL", quantity=5, position_ref=ref)

    refresh_pending_fills(
        graph,
        (_broker_fill(key, "AAPL", 5, Decimal("102.00"), "filled"),),
        sink,
    )

    node = graph.get_node("Fill", key)
    assert node is not None
    assert node.props["realized_pnl_cents"] == 700
    assert sink.faults == []


def test_partial_multi_lot_exit_needs_policy_and_writes_no_realized_pnl() -> None:
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    _position(graph, "a:AAPL", "AAPL", quantity=2, opened_price_cents=10000)
    _position(graph, "b:AAPL", "AAPL", quantity=3, opened_price_cents=10100)
    ref = open_positions(graph)[0].position_ref
    key = _pending_sell(graph, "AAPL", quantity=5, position_ref=ref)

    refresh_pending_fills(
        graph,
        (_broker_fill(key, "AAPL", 2, Decimal("102.00"), "partial"),),
        sink,
    )

    node = graph.get_node("Fill", key)
    assert node is not None
    assert "realized_pnl_cents" not in node.props
    assert sink.faults[0].message.endswith("entry basis unresolved")


def _position(
    graph: InMemoryGraphStore,
    key: str,
    ticker: str,
    *,
    quantity: int,
    opened_price_cents: int,
) -> None:
    graph.merge_node(
        "Position",
        key,
        {
            "ticker": ticker,
            "quantity": quantity,
            "opened_price_cents": opened_price_cents,
            "status": "open",
        },
    )


def _pending_sell(
    graph: InMemoryGraphStore, ticker: str, *, quantity: int, position_ref: str
) -> str:
    key = f"exit:{position_ref}:{ticker}:sell"
    order = graph.merge_node(
        "OrderIntent",
        f"pm-run:{ticker}",
        {
            "ticker": ticker,
            "action": "sell",
            "quantity": quantity,
            "position_ref": position_ref,
        },
    )
    fill = graph.merge_node(
        "Fill",
        key,
        {
            "ticker": ticker,
            "side": "sell",
            "quantity": quantity,
            "price_cents": 1,
            "broker_order_id": f"paper:{key}",
            "status": "pending",
        },
    )
    graph.add_edge(fill, order, "EXECUTES")
    return key


def _broker_fill(
    key: str,
    ticker: str,
    quantity: int,
    price: Decimal,
    status: Literal["filled", "partial"],
) -> BrokerFill:
    return BrokerFill(
        idempotency_key=key,
        ticker=ticker,
        side="sell",
        quantity=quantity,
        price=Money(amount=price),
        broker_order_id=f"paper:{key}",
        status=status,
    )
