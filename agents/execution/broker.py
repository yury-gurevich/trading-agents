"""Paper broker port and deterministic in-process implementation.

Agent: execution
Role: isolate broker submission behind an idempotent execution-owned port.
External I/O: none for PaperBroker; real broker clients land in a later sprint.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal, Protocol

from contracts.common import Money, Ticker

BASIS_POINTS_PER_UNIT = Decimal("10000")
CENT = Decimal("0.01")
ONE = Decimal("1")
ZERO = Decimal("0")


@dataclass(frozen=True)
class BrokerFill:
    """Broker-side order outcome retained under one idempotency key."""

    idempotency_key: str
    ticker: Ticker
    side: Literal["buy", "sell"]
    quantity: int
    price: Money
    broker_order_id: str
    status: Literal["filled", "partial", "rejected", "pending"]
    reason: str | None = None


@dataclass(frozen=True)
class BrokerPosition:
    """Broker-side holding snapshot, with money normalized to integer cents."""

    ticker: Ticker
    quantity: int
    avg_entry_cents: int
    market_value_cents: int


class BrokerRejectedError(RuntimeError):
    """Raised when the broker rejects while still returning an auditable outcome."""

    def __init__(self, fill: BrokerFill) -> None:
        """Keep the rejected fill available after fault recording."""
        super().__init__(fill.reason or "broker_rejected")
        self.fill = fill


class Broker(Protocol):
    """Execution-owned broker port."""

    def submit(
        self,
        idempotency_key: str,
        ticker: Ticker,
        side: Literal["buy", "sell"],
        quantity: int,
        limit_price: Money,
    ) -> BrokerFill:
        """Submit one order under a stable idempotency key."""
        ...  # pragma: no cover - protocol declaration only.

    def fills(self) -> tuple[BrokerFill, ...]:
        """Return broker-known outcomes for reconciliation."""
        ...  # pragma: no cover - protocol declaration only.

    def positions(self) -> tuple[BrokerPosition, ...]:
        """Return read-only broker holdings for graph reconciliation."""
        ...  # pragma: no cover - protocol declaration only.


class PaperBroker:
    """Deterministic in-process paper broker for the paper execution stage."""

    def __init__(
        self,
        *,
        slippage_bps: int = 0,
        reject_tickers: set[Ticker] | None = None,
    ) -> None:
        """Create a broker that de-dupes by idempotency key."""
        self._slippage_bps = slippage_bps
        self._reject_tickers = reject_tickers or set()
        self._fills: dict[str, BrokerFill] = {}

    @property
    def order_count(self) -> int:
        """Return the number of unique idempotency keys seen by this broker."""
        return len(self._fills)

    def submit(
        self,
        idempotency_key: str,
        ticker: Ticker,
        side: Literal["buy", "sell"],
        quantity: int,
        limit_price: Money,
    ) -> BrokerFill:
        """Fill immediately at the deterministic paper price, or return a replay."""
        current = self._fills.get(idempotency_key)
        if current is not None:
            if current.status == "rejected":
                raise BrokerRejectedError(current)
            return current
        if ticker in self._reject_tickers:
            fill = BrokerFill(
                idempotency_key=idempotency_key,
                ticker=ticker,
                side=side,
                quantity=quantity,
                price=limit_price,
                broker_order_id=f"paper:{idempotency_key}",
                status="rejected",
                reason="paper_broker_rejected",
            )
            self._fills[idempotency_key] = fill
            raise BrokerRejectedError(fill)
        fill = BrokerFill(
            idempotency_key=idempotency_key,
            ticker=ticker,
            side=side,
            quantity=quantity,
            price=_paper_price(limit_price, side, self._slippage_bps),
            broker_order_id=f"paper:{idempotency_key}",
            status="filled",
        )
        self._fills[idempotency_key] = fill
        return fill

    def fills(self) -> tuple[BrokerFill, ...]:
        """Return all unique broker outcomes in insertion order."""
        return tuple(self._fills.values())

    def positions(self) -> tuple[BrokerPosition, ...]:
        """Return the in-memory book implied by filled paper outcomes."""
        return _positions_from_fills(tuple(self._fills.values()))


def _paper_price(
    limit_price: Money, side: Literal["buy", "sell"], slippage_bps: int
) -> Money:
    adjustment = Decimal(slippage_bps) / BASIS_POINTS_PER_UNIT
    multiplier = ONE + adjustment if side == "buy" else max(ZERO, ONE - adjustment)
    amount = (limit_price.amount * multiplier).quantize(CENT, rounding=ROUND_HALF_UP)
    return Money(amount=amount, currency=limit_price.currency)


def _positions_from_fills(fills: tuple[BrokerFill, ...]) -> tuple[BrokerPosition, ...]:
    book: dict[Ticker, tuple[int, int]] = {}
    for fill in fills:
        if fill.status not in ("filled", "partial") or fill.quantity <= 0:
            continue
        qty, cost_cents = book.get(fill.ticker, (0, 0))
        price_cents = _money_to_cents(fill.price)
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


def _sell_from_book(qty: int, cost_cents: int, sold: int) -> tuple[int, int]:
    if sold >= qty or qty <= 0:
        return (0, 0)
    avg_entry_cents = round(cost_cents / qty)
    return (qty - sold, cost_cents - sold * avg_entry_cents)


def _money_to_cents(money: Money) -> int:
    cents = (money.amount * Decimal("100")).quantize(ONE, rounding=ROUND_HALF_UP)
    return int(cents)
