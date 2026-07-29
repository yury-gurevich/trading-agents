"""Seeded paper broker helper for orchestration tests.

Agent: orchestration
Role: expose starting broker holdings without adding seed fills.
External I/O: none.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

from agents.execution.broker import BrokerFill, BrokerPosition
from agents.execution.paper_broker import PaperBroker

if TYPE_CHECKING:
    from contracts.common import Money, Ticker

START_PRICE_CENTS = 10000
ONE = Decimal("1")


class SeededPaperBroker(PaperBroker):
    """Paper broker with a mutable starting book outside the submitted fills."""

    def __init__(
        self,
        positions: dict[Ticker, int],
        *,
        reject_tickers: set[Ticker] | None = None,
    ) -> None:
        super().__init__(reject_tickers=reject_tickers)
        self._seeded = dict(positions)

    def set_position(self, ticker: Ticker, quantity: int) -> None:
        """Update the starting book for the next broker-truth snapshot."""
        if quantity <= 0:
            self._seeded.pop(ticker, None)
            return
        self._seeded[ticker] = quantity

    def positions(self) -> tuple[BrokerPosition, ...]:
        """Return seeded holdings plus the effect of broker fills."""
        book = {
            ticker: (quantity, quantity * START_PRICE_CENTS)
            for ticker, quantity in self._seeded.items()
            if quantity > 0
        }
        for fill in self.fills():
            _apply_fill(book, fill)
        return tuple(
            BrokerPosition(
                ticker=ticker,
                quantity=quantity,
                avg_entry_cents=round(cost_cents / quantity),
                market_value_cents=cost_cents,
            )
            for ticker, (quantity, cost_cents) in sorted(book.items())
            if quantity > 0
        )


def _apply_fill(book: dict[Ticker, tuple[int, int]], fill: BrokerFill) -> None:
    if fill.status not in ("filled", "partial") or fill.quantity <= 0:
        return
    quantity, cost_cents = book.get(fill.ticker, (0, 0))
    price_cents = _money_to_cents(fill.price)
    if fill.side == "buy":
        book[fill.ticker] = (
            quantity + fill.quantity,
            cost_cents + fill.quantity * price_cents,
        )
        return
    remaining = quantity - fill.quantity
    if remaining <= 0:
        book.pop(fill.ticker, None)
        return
    avg_entry_cents = round(cost_cents / quantity)
    book[fill.ticker] = (remaining, cost_cents - fill.quantity * avg_entry_cents)


def _money_to_cents(fill_price: Money) -> int:
    cents = (fill_price.amount * Decimal("100")).quantize(ONE, rounding=ROUND_HALF_UP)
    return int(cents)
