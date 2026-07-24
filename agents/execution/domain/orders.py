"""Order and fill transformations for execution.

Agent: execution
Role: build idempotent broker submissions and contract fills deterministically.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from agents.execution.broker import BrokerFill
from contracts.execution import Fill

if TYPE_CHECKING:
    from contracts.common import Money, Ticker
    from contracts.portfolio_manager import OrderIntent, OrderIntentSet


@dataclass(frozen=True)
class BrokerOrder:
    """One broker submission derived from a contract payload."""

    idempotency_key: str
    ticker: Ticker
    side: Literal["buy", "sell"]
    quantity: int
    limit_price: Money


def order_from_intent(order_set: OrderIntentSet, intent: OrderIntent) -> BrokerOrder:
    """Build the stable paper-broker order for one approved intent."""
    side = _broker_side(intent.action)
    idempotency_key = f"{order_set.run_id}:{intent.ticker}:{side}"
    if intent.action == "sell" and intent.position_ref is not None:
        idempotency_key = f"exit:{intent.position_ref}:{intent.ticker}:sell"
    return BrokerOrder(
        idempotency_key=idempotency_key,
        ticker=intent.ticker,
        side=side,
        quantity=intent.quantity,
        limit_price=intent.est_price,
    )


def fill_from_broker(fill: BrokerFill) -> Fill:
    """Map a broker outcome onto the public execution contract."""
    return Fill(
        ticker=fill.ticker,
        side=fill.side,
        quantity=fill.quantity,
        price=fill.price,
        broker_order_id=fill.broker_order_id,
        status=fill.status,
    )


def rejected_broker_fill(order: BrokerOrder, reason: str) -> BrokerFill:
    """Build a durable rejected outcome for a failed broker submission."""
    return BrokerFill(
        idempotency_key=order.idempotency_key,
        ticker=order.ticker,
        side=order.side,
        quantity=order.quantity,
        price=order.limit_price,
        broker_order_id=f"rejected:{order.idempotency_key}",
        status="rejected",
        reason=reason,
    )


def execution_run_id(prefix: str, source_run_id: str) -> str:
    """Return a deterministic execution run id for idempotent replays."""
    return f"execution-{prefix}-{source_run_id}"


def _broker_side(action: str) -> Literal["buy", "sell"]:
    if action == "buy":
        return "buy"
    if action == "sell":
        return "sell"
    raise ValueError("execution can submit only buy or sell order intents")
