"""Value types for researcher walk-forward backtests.

Agent: researcher
Role: carry pure simulation legs, results, and close-series lookup state.
External I/O: none.
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass


@dataclass(frozen=True)
class RebalanceLeg:
    """One rebalance-to-rebalance portfolio leg."""

    score_date: str
    exit_score_date: str
    holdings: tuple[str, ...]
    gross_return: float
    net_return: float
    turnover: float
    fill_count: int
    ic: float | None


@dataclass(frozen=True)
class BacktestResult:
    """Complete walk-forward result and full/holdout metrics."""

    returns: tuple[float, ...]
    legs: tuple[RebalanceLeg, ...]
    sharpe: float
    max_drawdown: float
    turnover: float
    ic_mean: float | None
    n_days: int
    window_start: str
    window_end: str
    holdout_sharpe: float | None
    holdout_ic_mean: float | None
    holdout_max_drawdown: float | None
    holdout_turnover: float | None
    holdout_n_days: int


Legs = tuple[RebalanceLeg, ...] | list[RebalanceLeg]


@dataclass(frozen=True)
class _Series:
    dates: tuple[str, ...]
    prices: tuple[float, ...]

    @classmethod
    def from_bars(cls, bars: list[tuple[str, float]]) -> _Series:
        ordered = tuple(sorted(bars, key=lambda item: item[0]))
        return cls(
            dates=tuple(date for date, _ in ordered),
            prices=tuple(price for _, price in ordered),
        )

    def next_price(self, after_date: str) -> float | None:
        index = bisect_right(self.dates, after_date)
        if index >= len(self.prices):
            return None
        return self.prices[index]
