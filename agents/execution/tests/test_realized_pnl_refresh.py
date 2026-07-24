"""Execution realized-PnL refresh tests.

Agent: execution
Role: prove broker-confirmed sell fills append realized PnL only from real basis.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from agents.execution.broker import BrokerFill
from agents.execution.reconciliation_store import refresh_pending_fills
from contracts.common import Money
from contracts.positions import open_positions
from kernel import CollectingFaultSink, GraphFaultSink, InMemoryGraphStore, Node


def test_confirmed_sell_fill_uses_fill_price_for_abt_realized_pnl() -> None:
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    key = _seed_exit(graph, "ABT", quantity=98, opened_price_cents=10078)

    refresh_pending_fills(
        graph,
        (_broker_fill(key, "ABT", "sell", 98, Decimal("101.35"), "filled"),),
        sink,
    )
    refresh_pending_fills(
        graph,
        (_broker_fill(key, "ABT", "sell", 98, Decimal("101.35"), "filled"),),
        sink,
    )

    node = graph.get_node("Fill", key)
    assert node is not None
    assert node.props["price_cents"] == 1
    assert node.props["broker_price_cents"] == 10135
    assert node.props["realized_pnl_cents"] == 5586
    assert sink.faults == []


def test_existing_broker_price_is_used_when_backfilling_realized_pnl() -> None:
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    key = _seed_exit(graph, "ABT", quantity=98, opened_price_cents=10078)
    graph.merge_node(
        "Fill", key, {"broker_status": "filled", "broker_price_cents": 10135}
    )

    refresh_pending_fills(
        graph,
        (_broker_fill(key, "ABT", "sell", 98, Decimal("101.36"), "filled"),),
        sink,
    )

    node = graph.get_node("Fill", key)
    assert node is not None
    assert node.props["broker_price_cents"] == 10135
    assert node.props["realized_pnl_cents"] == 5586


def test_unresolved_entry_basis_writes_no_realized_pnl_and_records_fault() -> None:
    graph = InMemoryGraphStore()
    sink = GraphFaultSink(graph, CollectingFaultSink())
    key = _pending_sell(graph, "ABT", quantity=98, position_ref="missing")

    refresh_pending_fills(
        graph,
        (_broker_fill(key, "ABT", "sell", 98, Decimal("101.35"), "filled"),),
        sink,
    )

    node = graph.get_node("Fill", key)
    assert node is not None
    assert "realized_pnl_cents" not in node.props
    faults = graph.list_nodes("Fault")
    assert faults[0].props["error_type"] == "UnresolvedEntryBasis"


def test_sell_fill_without_position_ref_records_fault() -> None:
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    key = _pending_sell(graph, "ABT", quantity=98, position_ref=None)

    refresh_pending_fills(
        graph,
        (_broker_fill(key, "ABT", "sell", 98, Decimal("101.35"), "filled"),),
        sink,
    )

    node = graph.get_node("Fill", key)
    assert node is not None
    assert "realized_pnl_cents" not in node.props
    assert sink.faults[0].message.endswith("missing position_ref")


def test_partial_fill_realizes_only_filled_quantity() -> None:
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    key = _seed_exit(graph, "ABT", quantity=98, opened_price_cents=10078)

    refresh_pending_fills(
        graph,
        (_broker_fill(key, "ABT", "sell", 25, Decimal("101.35"), "partial"),),
        sink,
    )

    node = graph.get_node("Fill", key)
    assert node is not None
    assert node.props["realized_pnl_cents"] == 1425
    assert sink.faults == []


def _seed_exit(
    graph: InMemoryGraphStore, ticker: str, *, quantity: int, opened_price_cents: int
) -> str:
    _position(graph, f"held:{ticker}", ticker, quantity, opened_price_cents)
    ref = open_positions(graph)[0].position_ref
    return _pending_sell(graph, ticker, quantity=quantity, position_ref=ref)


def _position(
    graph: InMemoryGraphStore,
    key: str,
    ticker: str,
    quantity: int,
    opened_price_cents: int,
) -> Node:
    return graph.merge_node(
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
    graph: InMemoryGraphStore, ticker: str, *, quantity: int, position_ref: str | None
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
            "price_currency": "USD",
            "broker_order_id": f"paper:{key}",
            "status": "pending",
            "reason": None,
        },
    )
    graph.add_edge(fill, order, "EXECUTES")
    return key


def _broker_fill(
    key: str,
    ticker: str,
    side: Literal["buy", "sell"],
    quantity: int,
    price: Decimal,
    status: Literal["filled", "partial"],
) -> BrokerFill:
    return BrokerFill(
        idempotency_key=key,
        ticker=ticker,
        side=side,
        quantity=quantity,
        price=Money(amount=price),
        broker_order_id=f"paper:{key}",
        status=status,
    )
