"""Portfolio state used by the Portfolio Manager.

Agent: portfolio_manager
Role: represent the current paper portfolio until execution/monitor own positions.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from contracts.common import Money, Ticker, _Frozen

if TYPE_CHECKING:
    from decimal import Decimal


class PortfolioState(_Frozen):
    """Cash plus open-position quantities for this first PM slice."""

    cash: Money
    positions: dict[Ticker, int] = Field(default_factory=dict)

    @property
    def value(self) -> Decimal:
        """Return portfolio value used for sizing in this slice."""
        return self.cash.amount


def default_portfolio(starting_cash: Decimal) -> PortfolioState:
    """Build the fresh paper portfolio used until live position state lands."""
    return PortfolioState(cash=Money(amount=starting_cash), positions={})
