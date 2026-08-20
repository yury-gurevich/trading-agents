"""Return-series and pairwise-correlation math for Portfolio Manager.

Agent: portfolio_manager
Role: compute close-to-close returns and Pearson correlation for held-book gates.
External I/O: none.
"""

from __future__ import annotations

from datetime import timedelta
from itertools import pairwise
from math import sqrt
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping
    from datetime import date

    from contracts.provider import OHLCVBar


def returns_by_ticker(
    bars: tuple[OHLCVBar, ...], lookback_days: int
) -> dict[str, dict[date, float]]:
    """Return close-to-close return series keyed by uppercased ticker."""
    latest = max((bar.bar_date for bar in bars), default=None)
    if latest is None:
        return {}
    start = latest - timedelta(days=lookback_days)
    grouped: dict[str, list[OHLCVBar]] = {}
    for bar in bars:
        if bar.bar_date >= start:
            grouped.setdefault(bar.ticker.upper(), []).append(bar)
    return {ticker: _returns(series) for ticker, series in grouped.items()}


def pair_correlation(
    left: Mapping[date, float], right: Mapping[date, float]
) -> tuple[float | None, int]:
    """Return Pearson correlation and overlapping return count."""
    xs: list[float] = []
    ys: list[float] = []
    for day, value in left.items():
        other = right.get(day)
        if other is not None:
            xs.append(value)
            ys.append(other)
    return _pearson(xs, ys), len(xs)


def _returns(series: list[OHLCVBar]) -> dict[date, float]:
    ordered = sorted(series, key=lambda bar: bar.bar_date)
    return {
        current.bar_date: current.close / previous.close - 1.0
        for previous, current in pairwise(ordered)
    }


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2:
        return None
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    if var_x == 0.0 or var_y == 0.0:
        return None
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True))
    return float(cov / sqrt(var_x * var_y))
