"""Shared S184 Portfolio Manager concentration fixtures.

Agent: portfolio_manager
Role: provide issuer, sector, and synthetic-correlation fixtures for S184 tests.
External I/O: none.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

from agents.portfolio_manager.tests.helpers import recommendation
from contracts.provider import OHLCVBar

if TYPE_CHECKING:
    from contracts.analyst import Recommendation
    from contracts.portfolio_manager import GateOutcome, RejectedOrder

ISSUERS = {"GOOG": "alphabet", "GOOGL": "alphabet"}
SECTORS = {
    "AAPL": "Technology",
    "MSFT": "Software",
    "AMZN": "Retail",
    "GOOG": "Media",
    "GOOGL": "Media",
}


def buy(ticker: str) -> Recommendation:
    """Return a buy recommendation with explicit reward/risk fields."""
    return recommendation(ticker).model_copy(
        update={"suggested_stop_pct": 0.05, "suggested_target_pct": 0.10}
    )


def gate(rejection: RejectedOrder, name: str) -> GateOutcome:
    """Return one named gate from a rejection."""
    return next(item for item in rejection.gate_report if item.name == name)


def correlated_bars(tickers: tuple[str, ...], *, days: int) -> tuple[OHLCVBar, ...]:
    """Return enough close-return history to produce high pairwise correlations."""
    returns = (0.01, -0.005, 0.012, -0.004, 0.008)
    all_bars: list[OHLCVBar] = []
    for ticker_index, ticker in enumerate(tickers):
        close = 100.0 + ticker_index
        for offset in range(days):
            if offset:
                close *= 1.0 + returns[offset % len(returns)]
            all_bars.append(_bar(ticker, offset, close))
    return tuple(all_bars)


def _bar(ticker: str, offset: int, close: float) -> OHLCVBar:
    day = date(2026, 1, 1) + timedelta(days=offset)
    return OHLCVBar(
        ticker=ticker,
        bar_date=day,
        open=close,
        high=close + 1.0,
        low=close - 1.0,
        close=close,
        volume=1_000_000,
    )
