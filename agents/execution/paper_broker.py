"""Deterministic in-process paper broker implementation.

Agent: execution
Role: simulate broker submissions and holdings for tests and paper execution.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from typing import TYPE_CHECKING, Literal

from agents.execution.broker import (
    BrokerAccount,
    BrokerFill,
    BrokerPosition,
)
from agents.execution.paper_broker_math import (
    account_from_fills,
    money_to_cents,
    paper_price,
    positions_from_fills,
    within_tolerance,
)
from agents.execution.paper_broker_orders import (
    reject_order,
    replace_stop_order,
    replay_order,
)
from contracts.common import Money

if TYPE_CHECKING:
    from contracts.common import Ticker

_DEFAULT_ACCOUNT_CASH = Money(amount=Decimal("100000.00"))


class PaperBroker:
    """Deterministic in-process paper broker for the paper execution stage."""

    def __init__(
        self,
        *,
        slippage_bps: int = 0,
        order_price_tolerance_bps: int = 0,
        reject_tickers: set[Ticker] | None = None,
        starting_cash: Money = _DEFAULT_ACCOUNT_CASH,
        stop_order_status: str = "new",
    ) -> None:
        """Create a broker that de-dupes by idempotency key.

        `stop_order_status` is the raw status a resting stop reports: `new`, or
        `accepted` as Alpaca shows a stop placed after the close (S230).
        """
        self._stop_order_status = stop_order_status
        self._slippage_bps = slippage_bps
        self._order_price_tolerance_bps = order_price_tolerance_bps
        self._reject_tickers = reject_tickers or set()
        self._initial_cash_cents = money_to_cents(starting_cash)
        self._fills: dict[str, BrokerFill] = {}
        self.cancelled: list[str] = []

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
        tolerance_bps: int | None = None,
    ) -> BrokerFill:
        """Fill immediately at the deterministic paper price, or return a replay."""
        current = self._fills.get(idempotency_key)
        if current is not None:
            return replay_order(current)
        if ticker in self._reject_tickers:
            reject_order(
                self._fills, idempotency_key, ticker, side, quantity, limit_price
            )
        simulated_price = paper_price(limit_price, side, self._slippage_bps)
        tolerance = (
            self._order_price_tolerance_bps if tolerance_bps is None else tolerance_bps
        )
        if not within_tolerance(limit_price, simulated_price, side, tolerance):
            fill = BrokerFill(
                idempotency_key=idempotency_key,
                ticker=ticker,
                side=side,
                quantity=quantity,
                price=limit_price,
                broker_order_id=f"paper:{idempotency_key}",
                status="pending",
                reason="outside_order_price_tolerance",
                order_type="limit",
                time_in_force="day",
            )
            self._fills[idempotency_key] = fill
            return fill
        fill = BrokerFill(
            idempotency_key=idempotency_key,
            ticker=ticker,
            side=side,
            quantity=quantity,
            price=simulated_price,
            broker_order_id=f"paper:{idempotency_key}",
            status="filled",
            order_type="limit",
            time_in_force="day",
        )
        self._fills[idempotency_key] = fill
        return fill

    def submit_stop(
        self,
        idempotency_key: str,
        ticker: Ticker,
        side: Literal["buy", "sell"],
        quantity: int,
        stop_price: Money,
        tif: str = "gtc",
    ) -> BrokerFill:
        """Rest a stop order without filling it immediately."""
        current = self._fills.get(idempotency_key)
        if current is not None:
            return replay_order(current)
        if ticker in self._reject_tickers:
            reject_order(
                self._fills, idempotency_key, ticker, side, quantity, stop_price
            )
        fill = BrokerFill(
            idempotency_key=idempotency_key,
            ticker=ticker,
            side=side,
            quantity=quantity,
            price=stop_price,
            broker_order_id=f"paper:{idempotency_key}",
            status="pending",
            order_type="stop",
            time_in_force=tif,
            order_status=self._stop_order_status,
        )
        self._fills[idempotency_key] = fill
        return fill

    def replace_stop(
        self, broker_order_id: str, stop_price_cents: int, *, idempotency_key: str
    ) -> BrokerFill:
        """Move a resting stop in place; an `accepted` order is refused (422)."""
        return replace_stop_order(
            self._fills, broker_order_id, stop_price_cents, idempotency_key
        )

    def cancel(self, broker_order_id: str) -> None:
        """Record cancellation of an open paper order."""
        if broker_order_id not in self.cancelled:
            self.cancelled.append(broker_order_id)
        for key, fill in tuple(self._fills.items()):
            if fill.broker_order_id == broker_order_id and fill.status == "pending":
                self._fills[key] = replace(fill, status="rejected", reason="canceled")

    def fills(self) -> tuple[BrokerFill, ...]:
        """Return all unique broker outcomes in insertion order."""
        return tuple(self._fills.values())

    def positions(self) -> tuple[BrokerPosition, ...]:
        """Return the in-memory book implied by filled paper outcomes."""
        return positions_from_fills(tuple(self._fills.values()))

    def account(self) -> BrokerAccount:
        """Return deterministic paper account state for run-start sizing facts."""
        return account_from_fills(tuple(self._fills.values()), self._initial_cash_cents)
