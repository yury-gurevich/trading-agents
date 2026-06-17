"""Scanner beta computation — systematic risk vs a benchmark.

Agent: scanner
Role: compute a candidate's beta (cov/var of aligned daily returns) deterministically.
External I/O: none.
"""

from __future__ import annotations

import statistics
from itertools import pairwise
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date

    from contracts.provider import OHLCVBar


def compute_beta(
    stock_bars: tuple[OHLCVBar, ...],
    benchmark_bars: tuple[OHLCVBar, ...],
    min_observations: int,
) -> float | None:
    """Return beta = cov(stock, benchmark) / var(benchmark) over aligned daily returns.

    ``None`` when fewer than ``min_observations`` aligned returns exist (at least two,
    needed for a variance) or the benchmark return variance is zero (beta undefined).
    """
    stock_returns, benchmark_returns = _aligned_returns(stock_bars, benchmark_bars)
    if len(benchmark_returns) < max(min_observations, 2):
        return None
    benchmark_variance = statistics.variance(benchmark_returns)
    if benchmark_variance == 0.0:
        return None
    return statistics.covariance(stock_returns, benchmark_returns) / benchmark_variance


def _aligned_returns(
    stock_bars: tuple[OHLCVBar, ...],
    benchmark_bars: tuple[OHLCVBar, ...],
) -> tuple[list[float], list[float]]:
    stock_closes = {bar.bar_date: bar.close for bar in stock_bars}
    benchmark_closes = {bar.bar_date: bar.close for bar in benchmark_bars}
    dates = sorted(stock_closes.keys() & benchmark_closes.keys())
    stock_returns: list[float] = []
    benchmark_returns: list[float] = []
    for previous, current in pairwise(dates):
        stock_returns.append(_daily_return(stock_closes, previous, current))
        benchmark_returns.append(_daily_return(benchmark_closes, previous, current))
    return stock_returns, benchmark_returns


def _daily_return(closes: dict[date, float], previous: date, current: date) -> float:
    return (closes[current] - closes[previous]) / closes[previous]
