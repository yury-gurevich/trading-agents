"""Paper-broker order bookkeeping: rejection, replay and the in-place stop replace.

Agent: execution
Role: keep paper order records out of the PaperBroker shell (split by S230).
External I/O: none.
"""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from typing import TYPE_CHECKING, Literal, NoReturn

from agents.execution.broker import BrokerFill, BrokerRejectedError
from contracts.common import Money

if TYPE_CHECKING:
    from contracts.common import Ticker

# Alpaca refuses to replace an order it has only `accepted`, measured on paper
# 2026-09-25: PATCH /v2/orders/{id} -> 422 "cannot replace order in accepted status".
REPLACEABLE_ORDER_STATUS = "new"
_CENTS = Decimal("100")


def reject_order(
    fills: dict[str, BrokerFill],
    idempotency_key: str,
    ticker: Ticker,
    side: Literal["buy", "sell"],
    quantity: int,
    price: Money,
) -> NoReturn:
    """Record a paper rejection under its key and raise it."""
    fill = BrokerFill(
        idempotency_key=idempotency_key,
        ticker=ticker,
        side=side,
        quantity=quantity,
        price=price,
        broker_order_id=f"paper:{idempotency_key}",
        status="rejected",
        reason="paper_broker_rejected",
        order_type="limit",
        time_in_force="day",
    )
    fills[idempotency_key] = fill
    raise BrokerRejectedError(fill)


def replay_order(fill: BrokerFill) -> BrokerFill:
    """Return a duplicate submission's first outcome, re-raising a rejection."""
    if fill.status == "rejected":
        raise BrokerRejectedError(fill)
    return fill


def replace_stop_order(
    fills: dict[str, BrokerFill],
    broker_order_id: str,
    stop_price_cents: int,
    idempotency_key: str,
) -> BrokerFill:
    """Swap one open stop for a new order at a new price, as Alpaca's PATCH does.

    The old order becomes `replaced` and the new one rests under
    `idempotency_key`: there is no moment with neither open.
    """
    for key, old in tuple(fills.items()):
        if old.broker_order_id != broker_order_id or old.status != "pending":
            continue
        if old.order_status != REPLACEABLE_ORDER_STATUS:
            message = f"422 cannot replace order in {old.order_status} status"
            raise RuntimeError(message)
        new = replace(
            old,
            idempotency_key=idempotency_key,
            price=Money(amount=Decimal(stop_price_cents) / _CENTS),
            broker_order_id=f"paper:{idempotency_key}",
        )
        fills[key] = replace(
            old, status="rejected", reason="replaced", order_status="replaced"
        )
        fills[idempotency_key] = new
        return new
    raise LookupError(f"no open paper order {broker_order_id}")
