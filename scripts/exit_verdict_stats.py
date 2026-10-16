"""EXP-022's statistic, its family interval and an arm's scored blocks (S282).

Agent: tooling
Role: annualised return and excess for a window or a rebuilt series, every arm's
      whole window, years and halves, and the interval over a family's challengers.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scripts.exit_verdict_rule import CHALLENGERS
from scripts.replay_verdict_stats import (
    SESSIONS_PER_YEAR,
    annualised_excess,
    performance,
    rebuild,
)
from scripts.replay_verdict_windows import Window, half_windows, year_windows

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence
    from datetime import date

    from scripts.replay_verdict_score import ArmSeries
    from scripts.replay_verdict_stats import Pair

R_KEY = "annualised_return_pts"
A_KEY = "annualised_excess_pts"
COMPARISONS = len(CHALLENGERS)  # Bonferroni over one family's challengers
_TAIL_PER_MILLE = 25  # 2.5 % a side before the family adjustment
_PER_MILLE = 1000


def annualised_return(metrics: Mapping[str, float]) -> float:
    """R = ((1 + P/100)^(252/n) - 1) x 100 from the reporter's metrics."""
    sessions = metrics["performance_sessions"]
    if sessions <= 0:
        return 0.0
    growth = 1.0 + metrics["portfolio_return_pct"] / 100.0
    return (growth ** (SESSIONS_PER_YEAR / sessions) - 1.0) * 100.0


def family_interval(
    values: Sequence[float], comparisons: int = COMPARISONS
) -> tuple[float, float]:
    """v[k] and v[B - 1 - k] with k = B x 25 // (1000 x comparisons)."""
    ordered = sorted(values)
    k = len(ordered) * _TAIL_PER_MILLE // (_PER_MILLE * comparisons)
    return ordered[k], ordered[len(ordered) - 1 - k]


def windows(arm: ArmSeries) -> dict[str, Any]:
    """The arm's whole window, its calendar years and its two halves."""
    whole = Window("whole", False, tuple(sorted(arm.points)))
    return {
        "whole": _row(whole, arm.closes),
        "years": [_row(window, arm.closes) for window in year_windows(arm.points)],
        "halves": [_row(window, arm.closes) for window in half_windows(arm.points)],
    }


def resampled(pairs: Sequence[Pair], order: Iterable[int]) -> tuple[float, float]:
    """R and A of the series rebuilt from `pairs` taken in `order`."""
    points, closes = rebuild(pairs, order)
    metrics = performance(points, closes)
    return annualised_return(metrics), annualised_excess(metrics)


def _row(window: Window, closes: Mapping[date, float]) -> dict[str, Any]:
    metrics = performance(window.points, closes)
    return {
        "label": window.label,
        "first": window.points[0][0].isoformat(),
        "last": window.points[-1][0].isoformat(),
        "partial": window.partial,
        **metrics,
        R_KEY: annualised_return(metrics),
        A_KEY: annualised_excess(metrics),
    }
