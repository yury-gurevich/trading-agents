"""Execution partial-fill completion tests.

Agent: execution
Role: prove a partial broker fill can finish without weakening terminal status.
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


def test_partial_broker_status_can_finish_with_final_price() -> None:
    """EXEC-STA-05 / EXEC-OBS-01: partial fills may advance to filled."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    first_refresh = "2026-08-13T00:00:00+00:00"
    key = _pending_fill(
        graph,
        "AAPL",
        "buy",
        broker_status="partial",
        broker_price_cents=10135,
        broker_status_refreshed_at=first_refresh,
    )

    refresh_pending_fills(
        graph,
        (_broker_fill(key, "AAPL", "buy", 1, Decimal("102.00"), "filled"),),
        sink,
    )

    fill = _fill(graph, key)
    assert fill.props["broker_status"] == "filled"
    assert fill.props["broker_price_cents"] == 10200
    assert fill.props["broker_status_refreshed_at"] != first_refresh
    assert len(graph.list_nodes("BrokerOrderStatus")) == 1


def test_terminal_broker_status_refuses_rewrite() -> None:
    """EXEC-STA-03 / EXEC-STA-05: terminal broker status is immutable."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    filled_key = _pending_fill(
        graph, "AAPL", "buy", broker_status="filled", broker_price_cents=10135
    )
    rejected_key = _pending_fill(
        graph, "MSFT", "buy", broker_status="rejected", broker_price_cents=9900
    )

    refresh_pending_fills(
        graph,
        (
            _broker_fill(filled_key, "AAPL", "buy", 1, Decimal("99.00"), "partial"),
            _broker_fill(rejected_key, "MSFT", "buy", 1, Decimal("100.00"), "filled"),
        ),
        sink,
    )

    assert _fill(graph, filled_key).props["broker_status"] == "filled"
    assert _fill(graph, filled_key).props["broker_price_cents"] == 10135
    assert _fill(graph, rejected_key).props["broker_status"] == "rejected"
    assert _fill(graph, rejected_key).props["broker_price_cents"] == 9900
    assert graph.list_nodes("BrokerOrderStatus") == ()


def test_completed_after_partial_sell_uses_final_price_for_realized_pnl() -> None:
    """EXEC-STA-05 / EXEC-OBS-01: final fill price is the sell PnL basis."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    key = _seed_exit(graph, "ABT", quantity=10, opened_price_cents=10000)

    refresh_pending_fills(
        graph,
        (_broker_fill(key, "ABT", "sell", 10, Decimal("101.35"), "partial"),),
        sink,
    )
    assert _fill(graph, key).props["realized_pnl_cents"] == 1350

    refresh_pending_fills(
        graph,
        (_broker_fill(key, "ABT", "sell", 10, Decimal("102.00"), "filled"),),
        sink,
    )

    node = _fill(graph, key)
    assert node.props["broker_status"] == "filled"
    assert node.props["broker_price_cents"] == 10200
    assert node.props["realized_pnl_cents"] == 2000
    assert sink.faults == []


def _seed_exit(
    graph: InMemoryGraphStore, ticker: str, *, quantity: int, opened_price_cents: int
) -> str:
    _position(graph, f"held:{ticker}", ticker, quantity, opened_price_cents)
    ref = open_positions(graph)[0].position_ref
    return _pending_fill(graph, ticker, "sell", quantity=quantity, position_ref=ref)


def _pending_fill(
    graph: InMemoryGraphStore,
    ticker: str,
    side: Literal["buy", "sell"],
    *,
    quantity: int = 1,
    position_ref: str | None = None,
    broker_status: str | None = None,
    broker_price_cents: int | None = None,
    broker_status_refreshed_at: str | None = None,
) -> str:
    key = f"run:{ticker}:{side}"
    props: dict[str, object] = {
        "ticker": ticker,
        "side": side,
        "quantity": quantity,
        "price_cents": 1,
        "price_currency": "USD",
        "broker_order_id": f"paper:{key}",
        "status": "pending",
        "reason": None,
    }
    if position_ref is not None:
        props["position_ref"] = position_ref
    if broker_status is not None:
        props["broker_status"] = broker_status
    if broker_price_cents is not None:
        props["broker_price_cents"] = broker_price_cents
    if broker_status_refreshed_at is not None:
        props["broker_status_refreshed_at"] = broker_status_refreshed_at
    graph.merge_node("Fill", key, props)
    return key


def _position(
    graph: InMemoryGraphStore,
    key: str,
    ticker: str,
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
    side: Literal["buy", "sell"],
    quantity: int,
    price: Decimal,
    status: Literal["filled", "partial", "rejected", "pending"],
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


def _fill(graph: InMemoryGraphStore, key: str) -> Node:
    fill = graph.get_node("Fill", key)
    assert fill is not None
    return fill
