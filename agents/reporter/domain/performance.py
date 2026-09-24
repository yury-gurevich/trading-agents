"""Pure benchmark-relative performance calculations.

Agent: reporter
Role: derive date-bounded portfolio and benchmark return metrics.
External I/O: none.
"""

from __future__ import annotations

from datetime import date
from itertools import pairwise
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

PerformancePoint = tuple[date, int, int]


def calculate_performance(
    points: Sequence[PerformancePoint],
    benchmark_closes: Mapping[date, float],
    *,
    rolling_sessions: int,
) -> dict[str, float]:
    """Return chained performance metrics from dated portfolio and benchmark facts."""
    ordered_points = sorted(points, key=lambda point: point[0])
    pairs, gap_sessions = _usable_pairs(ordered_points, benchmark_closes)
    if not pairs:
        return _empty_metrics(gap_sessions)

    portfolio_factor = 1.0
    benchmark_factor = 1.0
    exposure_factor = 1.0
    exposures: list[float] = []
    for previous, current, previous_close, current_close in pairs:
        previous_equity = previous[1]
        current_equity = current[1]
        benchmark_ratio = current_close / previous_close
        portfolio_factor *= current_equity / previous_equity
        benchmark_factor *= benchmark_ratio
        exposure = previous[2] / previous_equity
        exposure_factor *= 1.0 + exposure * (benchmark_ratio - 1.0)
        exposures.append(exposure)

    rolling_pairs = pairs[-rolling_sessions:]
    rolling_portfolio, rolling_exposure = _chained_factors(rolling_pairs)
    portfolio_return = _percent(portfolio_factor)
    exposure_return = _percent(exposure_factor)
    return {
        "portfolio_return_pct": portfolio_return,
        "benchmark_return_pct": _percent(benchmark_factor),
        "exposure_matched_return_pct": exposure_return,
        "excess_return_pct": portfolio_return - exposure_return,
        "average_exposure_pct": sum(exposures) / len(exposures) * 100.0,
        "max_drawdown_pct": _max_drawdown(ordered_points),
        "rolling_portfolio_return_pct": _percent(rolling_portfolio),
        "rolling_exposure_matched_return_pct": _percent(rolling_exposure),
        "rolling_excess_return_pct": _percent(rolling_portfolio)
        - _percent(rolling_exposure),
        "performance_sessions": float(len(pairs)),
        "performance_gap_sessions": float(gap_sessions),
        "equity_cents": float(ordered_points[-1][1]),
    }


def _usable_pairs(
    points: Sequence[PerformancePoint], benchmark_closes: Mapping[date, float]
) -> tuple[list[tuple[PerformancePoint, PerformancePoint, float, float]], int]:
    pairs: list[tuple[PerformancePoint, PerformancePoint, float, float]] = []
    gap_sessions = 0
    for previous, current in pairwise(points):
        previous_close = benchmark_closes.get(previous[0])
        current_close = benchmark_closes.get(current[0])
        if (
            previous_close is None
            or current_close is None
            or previous_close <= 0
            or current_close <= 0
            or previous[1] == 0
        ):
            gap_sessions += 1
            continue
        pairs.append((previous, current, previous_close, current_close))
    return pairs, gap_sessions


def _chained_factors(
    pairs: Sequence[tuple[PerformancePoint, PerformancePoint, float, float]],
) -> tuple[float, float]:
    portfolio_factor = 1.0
    exposure_factor = 1.0
    for previous, current, previous_close, current_close in pairs:
        portfolio_factor *= current[1] / previous[1]
        exposure = previous[2] / previous[1]
        exposure_factor *= 1.0 + exposure * (current_close / previous_close - 1.0)
    return portfolio_factor, exposure_factor


def _max_drawdown(points: Sequence[PerformancePoint]) -> float:
    peak_equity = points[0][1]
    drawdown = 0.0
    for _day, equity_cents, _long_value_cents in points:
        peak_equity = max(peak_equity, equity_cents)
        if peak_equity:
            drawdown = min(drawdown, equity_cents / peak_equity - 1.0)
    return drawdown * 100.0


def _empty_metrics(gap_sessions: int) -> dict[str, float]:
    return {
        "portfolio_return_pct": 0.0,
        "benchmark_return_pct": 0.0,
        "exposure_matched_return_pct": 0.0,
        "excess_return_pct": 0.0,
        "average_exposure_pct": 0.0,
        "max_drawdown_pct": 0.0,
        "rolling_portfolio_return_pct": 0.0,
        "rolling_exposure_matched_return_pct": 0.0,
        "rolling_excess_return_pct": 0.0,
        "performance_sessions": 0.0,
        "performance_gap_sessions": float(gap_sessions),
        "equity_cents": 0.0,
    }


def _percent(factor: float) -> float:
    return (factor - 1.0) * 100.0
