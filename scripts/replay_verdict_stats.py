"""The EXP-014 statistic, a resampled series' rebuild, and the bootstrap's draws (S250).

Agent: tooling
Role: score series only through calculate_performance; resample session pairs.
External I/O: none.
"""

from __future__ import annotations

import random
from datetime import date
from itertools import pairwise
from typing import TYPE_CHECKING

from agents.reporter.domain.performance import calculate_performance

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

Point = tuple[date, int, int]
# (equity before, equity after, invested before, SPY before, SPY after) for one pair.
Pair = tuple[int, int, int, float, float]

ROLLING_SESSIONS = 20  # the reporter's `performance_rolling_sessions`
SESSIONS_PER_YEAR = 252  # Appendix P's annualisation
REBUILD_START_CENTS = 10**14  # DL-258 D5: a rebuild's first equity, in cents
_FIRST_ORDINAL = 1  # a rebuilt series' dates are consecutive ordinals from here
# The interval's tails: 2.5 % each side, as integer per-mille (DL-258 D3).
_TAIL_PER_MILLE = 25
_PER_MILLE = 1000


def performance(
    points: Sequence[Point], closes: Mapping[date, float]
) -> dict[str, float]:
    """The reporter's metrics: the only place a return is computed (RPT-OUT-07)."""
    return calculate_performance(points, closes, rolling_sessions=ROLLING_SESSIONS)


def annualised_excess(metrics: Mapping[str, float]) -> float:
    """A = ((1 + P/100)^(252/n) - (1 + E/100)^(252/n)) x 100 from the metrics."""
    sessions = metrics["performance_sessions"]
    if sessions <= 0:
        return 0.0
    power = SESSIONS_PER_YEAR / sessions
    portfolio = (1.0 + metrics["portfolio_return_pct"] / 100.0) ** power
    matched = (1.0 + metrics["exposure_matched_return_pct"] / 100.0) ** power
    return (portfolio - matched) * 100.0


def arm_pairs(
    points: Sequence[Point], closes: Mapping[date, float]
) -> tuple[Pair, ...]:
    """Each consecutive session pair as raw facts; scoring never reads them directly."""
    return tuple(
        (before[1], after[1], before[2], closes[before[0]], closes[after[0]])
        for before, after in pairwise(sorted(points))
    )


def rebuild(
    pairs: Sequence[Pair], order: Iterable[int]
) -> tuple[list[Point], dict[date, float]]:
    """Points and SPY closes for the pairs taken in `order` (DL-258 D5)."""
    equity, close, ordinal = REBUILD_START_CENTS, 1.0, _FIRST_ORDINAL
    points: list[Point] = []
    closes: dict[date, float] = {}
    for index in order:
        before, after, invested, spy_before, spy_after = pairs[index]
        day = date.fromordinal(ordinal)
        points.append((day, equity, _scaled(equity, invested, before)))
        closes[day] = close
        equity = _scaled(equity, after, before)
        close = close * spy_after / spy_before
        ordinal += 1
    day = date.fromordinal(ordinal)
    points.append((day, equity, 0))
    closes[day] = close
    return points, closes


def replica_pairs(pairs: Sequence[Pair]) -> tuple[Pair, ...]:
    """The control: SPY earned at the arm's own exposure, pair by pair."""
    out: list[Pair] = []
    for before, _after, invested, spy_before, spy_after in pairs:
        start = REBUILD_START_CENTS
        held = _scaled(start, invested, before)
        end = start + round(held * (spy_after / spy_before - 1.0))
        out.append((start, end, held, spy_before, spy_after))
    return tuple(out)


def seeded(seed: int) -> random.Random:
    """The one random source: `random.Random(seed)`, never the module functions."""
    return random.Random(seed)  # noqa: S311 - seeded resampling, not cryptography.


def stationary_draws(count: int, mean_block: int, rng: random.Random) -> list[int]:
    """One stationary-bootstrap resample of `count` pair indices (DL-258 D3)."""
    restart = 1.0 / mean_block
    index = rng.randrange(count)
    draws = [index]
    while len(draws) < count:
        fresh = rng.random() < restart
        index = rng.randrange(count) if fresh else (index + 1) % count
        draws.append(index)
    return draws


def percentile_interval(values: Sequence[float]) -> tuple[float, float]:
    """The 2.5th and 97.5th percentiles: v[k] and v[B - 1 - k], k = B x 25 // 1000."""
    ordered = sorted(values)
    k = len(ordered) * _TAIL_PER_MILLE // _PER_MILLE
    return ordered[k], ordered[len(ordered) - 1 - k]


def _scaled(value: int, numerator: int, denominator: int) -> int:
    """round(value x numerator / denominator) in integer arithmetic, half up."""
    return (2 * value * numerator + denominator) // (2 * denominator)
