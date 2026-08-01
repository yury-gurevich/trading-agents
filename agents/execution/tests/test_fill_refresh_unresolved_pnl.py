"""Execution unresolved-PnL refresh tests.

Agent: execution
Role: prove unresolved sell-fill basis faults are recorded once.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from agents.execution.broker import BrokerFill
from agents.execution.reconciliation_store import refresh_pending_fills
from contracts.common import Money
from contracts.positions import open_positions
from kernel import CollectingFaultSink, InMemoryGraphStore, Node


def test_missing_position_ref_records_one_unresolved_pnl_marker() -> None:
    """EXEC-FAIL-03 / EXEC-IDM-01: unresolved missing ref faults once."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    key = _pending_sell(graph, "ABT")
    fills = (_broker_fill(key, "ABT", 98, "partial"),)

    refresh_pending_fills(graph, fills, sink)
    first_marker = _fill(graph, key).props["pnl_unresolved_at"]
    refresh_pending_fills(graph, fills, sink)

    fill = _fill(graph, key)
    assert "realized_pnl_cents" not in fill.props
    assert fill.props["pnl_unresolved_at"] == first_marker
    assert [fault.error_type for fault in sink.faults] == ["UnresolvedEntryBasis"]
    assert sink.faults[0].message.endswith("missing position_ref")


def test_unresolved_entry_basis_records_one_marker_and_fault() -> None:
    """EXEC-FAIL-03 / EXEC-OBS-02: unresolved basis is durable evidence."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    key = _pending_sell_with_order(graph, "ABT", quantity=98, position_ref="missing")

    refresh_pending_fills(graph, (_broker_fill(key, "ABT", 98, "filled"),), sink)

    fill = _fill(graph, key)
    assert "realized_pnl_cents" not in fill.props
    assert isinstance(fill.props["pnl_unresolved_at"], str)
    assert sink.faults[0].message.endswith("entry basis unresolved")


def test_amd_exit_shape_still_realizes_pnl_without_unresolved_marker() -> None:
    """EXEC-STA-03 / EXEC-OBS-01: resolvable AMD-shaped sell PnL is unchanged."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    key = _amd_exit_shape(graph)

    refresh_pending_fills(graph, (_broker_fill(key, "AMD", 55, "filled"),), sink)

    fill = _fill(graph, key)
    assert fill.props["realized_pnl_cents"] == -351560
    assert "pnl_unresolved_at" not in fill.props
    assert sink.faults == []


def _pending_sell(graph: InMemoryGraphStore, ticker: str) -> str:
    key = f"run:{ticker}:sell"
    graph.merge_node(
        "Fill",
        key,
        {
            "ticker": ticker,
            "side": "sell",
            "quantity": 98,
            "price_cents": 1,
            "price_currency": "USD",
            "broker_order_id": f"paper:{key}",
            "status": "pending",
            "reason": None,
        },
    )
    return key


def _pending_sell_with_order(
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
            "price_currency": "USD",
            "broker_order_id": f"paper:{key}",
            "status": "pending",
            "reason": None,
        },
    )
    graph.add_edge(fill, order, "EXECUTES")
    return key


def _amd_exit_shape(graph: InMemoryGraphStore) -> str:
    _position(graph, "held:AMD", "AMD", quantity=55, opened_price_cents=53127)
    ref = open_positions(graph)[0].position_ref
    return _pending_sell_with_order(graph, "AMD", quantity=55, position_ref=ref)


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


def _broker_fill(
    key: str,
    ticker: str,
    quantity: int,
    status: Literal["filled", "partial"],
) -> BrokerFill:
    return BrokerFill(
        idempotency_key=key,
        ticker=ticker,
        side="sell",
        quantity=quantity,
        price=Money(amount=Decimal("467.35")),
        broker_order_id=f"paper:{key}",
        status=status,
    )


def _fill(graph: InMemoryGraphStore, key: str) -> Node:
    fill = graph.get_node("Fill", key)
    assert fill is not None
    return fill
