"""Broker port and shared broker outcome types.

Agent: execution
Role: isolate broker submission behind an idempotent execution-owned port.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol

if TYPE_CHECKING:
    from contracts.common import Money, Ticker

OrderToleranceMode = Literal["flat", "scaled"]


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
    submitted_at: str | None = None
    order_type: str | None = None
    time_in_force: str | None = None
    order_tolerance_mode: OrderToleranceMode | None = None
    order_counterfactual_mode: OrderToleranceMode | None = None
    order_decided_price: Money | None = None
    order_applied_tolerance_bps: int | None = None
    order_applied_limit_price: Money | None = None
    order_counterfactual_tolerance_bps: int | None = None
    order_counterfactual_limit_price: Money | None = None
    order_flat_tolerance_bps: int | None = None
    order_flat_limit_price: Money | None = None
    order_scaled_tolerance_bps: int | None = None
    order_scaled_limit_price: Money | None = None
    order_decision_atr_pct: float | None = None
    order_volatility_present: bool | None = None
    order_volatility_fallback: bool | None = None


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
        tolerance_bps: int | None = None,
    ) -> BrokerFill:
        """Submit one order under a stable idempotency key."""
        ...  # pragma: no cover - protocol declaration only.

    def submit_stop(
        self,
        idempotency_key: str,
        ticker: Ticker,
        side: Literal["buy", "sell"],
        quantity: int,
        stop_price: Money,
        tif: str = "gtc",
    ) -> BrokerFill:
        """Submit one resting stop order under a stable idempotency key."""
        ...  # pragma: no cover - protocol declaration only.

    def cancel(self, broker_order_id: str) -> None:
        """Cancel one open broker order by broker id."""
        ...  # pragma: no cover - protocol declaration only.

    def fills(self) -> tuple[BrokerFill, ...]:
        """Return broker-known outcomes for reconciliation."""
        ...  # pragma: no cover - protocol declaration only.

    def positions(self) -> tuple[BrokerPosition, ...]:
        """Return read-only broker holdings for graph reconciliation."""
        ...  # pragma: no cover - protocol declaration only.


__all__ = [
    "Broker",
    "BrokerFill",
    "BrokerPosition",
    "BrokerRejectedError",
]
