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


def _paper_price(
    limit_price: Money, side: Literal["buy", "sell"], slippage_bps: int
) -> Money:
    adjustment = Decimal(slippage_bps) / BASIS_POINTS_PER_UNIT
    multiplier = ONE + adjustment if side == "buy" else max(ZERO, ONE - adjustment)
    amount = (limit_price.amount * multiplier).quantize(CENT, rounding=ROUND_HALF_UP)
    return Money(amount=amount, currency=limit_price.currency)
