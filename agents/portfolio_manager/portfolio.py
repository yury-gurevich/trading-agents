"""Portfolio state used by the Portfolio Manager.

Agent: portfolio_manager
Role: represent the current paper portfolio until execution/monitor own positions.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import Field

from contracts.common import Money, Ticker, _Frozen


class PortfolioState(_Frozen):
    """Cash plus open-position quantities for this first PM slice."""

    cash: Money
    positions: dict[Ticker, int] = Field(default_factory=dict)
    position_refs: dict[Ticker, str] = Field(default_factory=dict)
    position_values: dict[Ticker, Money] = Field(default_factory=dict)
    account_status: Literal["fresh", "stale"] = "fresh"
    account_stale_reason: str | None = None
    account_cash_cents: int | None = None
    account_equity_cents: int | None = None
    account_buying_power_cents: int | None = None

    @property
    def value(self) -> Decimal:
        """Return the equity-backed portfolio value used for sizing."""
        return self.cash.amount

    @property
    def deployed_value(self) -> Decimal:
        """Return the account value already deployed into open positions."""
        return sum(
            (item.amount for item in self.position_values.values()), Decimal("0")
        )

    @property
    def account_is_fresh(self) -> bool:
        """Return whether account-backed sizing facts are fresh enough for buys."""
        return self.account_status == "fresh"

    def available_for_buys(
        self, cash_buffer_pct: Decimal, reserved_cash: Decimal
    ) -> Decimal:
        """Return equity not already deployed or reserved by this PM run."""
        if not self.account_is_fresh:
            return Decimal("0")
        return self.value * (Decimal("1") - cash_buffer_pct) - (
            self.deployed_value + reserved_cash
        )


def default_portfolio(starting_cash: Decimal) -> PortfolioState:
    """Build the fresh paper portfolio used until live position state lands."""
    return PortfolioState(
        cash=Money(amount=starting_cash), positions={}, position_refs={}
    )
