"""Paper broker money and position reducers.

Agent: execution
Role: keep deterministic paper price and book math out of the broker shell.
External I/O: none.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from agents.execution.broker import BrokerAccount, BrokerFill, BrokerPosition
from contracts.common import Money, Ticker

BASIS_POINTS_PER_UNIT = Decimal("10000")
CENT = Decimal("0.01")
ONE = Decimal("1")
ZERO = Decimal("0")


def paper_price(
    limit_price: Money, side: Literal["buy", "sell"], slippage_bps: int
) -> Money:
    """Return the deterministic paper execution price."""
    adjustment = Decimal(slippage_bps) / BASIS_POINTS_PER_UNIT
    multiplier = ONE + adjustment if side == "buy" else max(ZERO, ONE - adjustment)
    amount = (limit_price.amount * multiplier).quantize(CENT, rounding=ROUND_HALF_UP)
    return Money(amount=amount, currency=limit_price.currency)


def within_tolerance(
    reference: Money,
    execution_price: Money,
    side: Literal["buy", "sell"],
    tolerance_bps: int,
) -> bool:
    """Return whether the simulated execution price is inside the order band."""
    tolerance = Decimal(tolerance_bps) / BASIS_POINTS_PER_UNIT
    if side == "buy":
        return execution_price.amount <= reference.amount * (ONE + tolerance)
    return execution_price.amount >= reference.amount * max(ZERO, ONE - tolerance)


def positions_from_fills(fills: tuple[BrokerFill, ...]) -> tuple[BrokerPosition, ...]:
    """Return the in-memory book implied by filled paper outcomes."""
    book: dict[Ticker, tuple[int, int]] = {}
    for fill in fills:
        if fill.status not in ("filled", "partial") or fill.quantity <= 0:
            continue
        qty, cost_cents = book.get(fill.ticker, (0, 0))
        price_cents = money_to_cents(fill.price)
        if fill.side == "buy":
            qty += fill.quantity
            cost_cents += fill.quantity * price_cents
        else:
            qty, cost_cents = _sell_from_book(qty, cost_cents, fill.quantity)
        if qty > 0:
            book[fill.ticker] = (qty, cost_cents)
        else:
            book.pop(fill.ticker, None)
    return tuple(
        BrokerPosition(
            ticker=ticker,
            quantity=qty,
            avg_entry_cents=round(cost_cents / qty),
            market_value_cents=cost_cents,
        )
        for ticker, (qty, cost_cents) in sorted(book.items())
    )


def account_from_fills(
    fills: tuple[BrokerFill, ...], initial_cash_cents: int
) -> BrokerAccount:
    """Return deterministic account state implied by paper fills."""
    cash_cents = initial_cash_cents
    for fill in fills:
        if fill.status not in ("filled", "partial") or fill.quantity <= 0:
            continue
        delta = money_to_cents(fill.price) * fill.quantity
        cash_cents += delta if fill.side == "sell" else -delta
    market_value_cents = sum(
        position.market_value_cents for position in positions_from_fills(fills)
    )
    return BrokerAccount(
        cash_cents=cash_cents,
        equity_cents=cash_cents + market_value_cents,
        buying_power_cents=max(cash_cents, 0),
    )


def money_to_cents(money: Money) -> int:
    """Return whole cents using the repo money rounding convention."""
    cents = (money.amount * Decimal("100")).quantize(ONE, rounding=ROUND_HALF_UP)
    return int(cents)


def _sell_from_book(qty: int, cost_cents: int, sold: int) -> tuple[int, int]:
    if sold >= qty or qty <= 0:
        return (0, 0)
    avg_entry_cents = round(cost_cents / qty)
    return (qty - sold, cost_cents - sold * avg_entry_cents)
