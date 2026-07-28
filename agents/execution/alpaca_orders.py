"""Alpaca order payload and response mapping helpers.

Agent: execution
Role: keep Alpaca REST payload details out of the broker adapter shell.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from agents.execution.broker import BrokerFill
from contracts.common import Money

_PENDING = frozenset({"new", "accepted", "pending_new", "held", "accepted_for_bidding"})

BrokerStatus = Literal["filled", "partial", "rejected", "pending"]
BrokerSide = Literal["buy", "sell"]


def order_body(
    idempotency_key: str, ticker: str, side: BrokerSide, quantity: int
) -> dict[str, object]:
    """Return an Alpaca market-order payload."""
    return {
        "symbol": str(ticker),
        "qty": str(quantity),
        "side": side,
        "type": "market",
        "time_in_force": "day",
        "client_order_id": idempotency_key,
    }


def stop_order_body(
    idempotency_key: str,
    ticker: str,
    side: BrokerSide,
    quantity: int,
    stop_price: Money,
    tif: str,
) -> dict[str, object]:
    """Return an Alpaca stop-order payload."""
    return {
        "symbol": str(ticker),
        "qty": str(quantity),
        "side": side,
        "type": "stop",
        "stop_price": str(stop_price.amount),
        "time_in_force": tif,
        "client_order_id": idempotency_key,
    }


def fill_from_order(
    order: object, idempotency_key: str, reference: Money
) -> BrokerFill:
    """Map an Alpaca order object onto a BrokerFill; never raise on a dict."""
    if not isinstance(order, dict):
        return rejected(idempotency_key, reference, "malformed_broker_response")
    status = status_of(str(order.get("status", "")))
    return BrokerFill(
        idempotency_key=idempotency_key,
        ticker=str(order.get("symbol", "")),
        side=side_of(str(order.get("side", "buy"))),
        quantity=int(float(str(order.get("qty", 0)))),
        price=price_of(order, reference),
        broker_order_id=str(order.get("id", "")),
        status=status,
        reason=str(order.get("status", "rejected")) if status == "rejected" else None,
        submitted_at=_optional_str(order.get("submitted_at")),
    )


def rejected(idempotency_key: str, reference: Money, reason: str) -> BrokerFill:
    """Return a rejected fill for malformed Alpaca responses."""
    return BrokerFill(
        idempotency_key=idempotency_key,
        ticker="",
        side="buy",
        quantity=0,
        price=reference,
        broker_order_id="",
        status="rejected",
        reason=reason,
    )


def status_of(raw: str) -> BrokerStatus:
    """Map Alpaca order status onto the broker contract status."""
    if raw == "filled":
        return "filled"
    if raw == "partially_filled":
        return "partial"
    if raw in _PENDING:
        return "pending"
    return "rejected"


def side_of(raw: str) -> BrokerSide:
    """Map Alpaca side strings onto the broker contract side."""
    return "sell" if raw == "sell" else "buy"


def price_of(order: dict[str, object], reference: Money) -> Money:
    """Return fill average when present, otherwise the caller's reference price."""
    raw = order.get("filled_avg_price")
    if raw in (None, ""):
        return reference
    return Money(amount=Decimal(str(raw)))


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) and value else None
