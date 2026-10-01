"""Synthetic arms for the S250 scorer tests.

Agent: tooling
Role: build invented equity and SPY series with a planted edge, null or deficit.
External I/O: none.

Nothing here is market data. SPY is a seeded random walk; an arm earns SPY at a
fixed exposure, plus a planted drift per session, plus seeded noise whose sample
mean is removed so the realised drift is exactly the planted one.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

from scripts.replay_verdict_score import ArmSeries
from scripts.replay_verdict_stats import seeded

from agents.provider.domain.market_calendar import is_trading_session

if TYPE_CHECKING:
    from scripts.replay_verdict_stats import Point

ARM_NAMES = (
    "base-05",
    "base-10",
    "base-25",
    "technical-only-25",
    "relative-strength-only-25",
)
EXPOSURE = 0.8
NOISE = 0.002  # daily: an annualised standard error of about 2.9 points over 300 pairs
EDGE_DRIFT = 0.001  # daily: about +28 points a year, near ten standard errors from 0
START_CENTS = 10_000_000


def trading_days(first: date, count: int) -> tuple[date, ...]:
    """`count` NYSE sessions from `first` on."""
    day, out = first, []
    while len(out) < count:
        if is_trading_session(day):
            out.append(day)
        day += timedelta(days=1)
    return tuple(out)


def spy_closes(days: tuple[date, ...], seed: int = 7) -> dict[date, float]:
    """A seeded random walk for SPY, 1 % a day."""
    rng, close, out = seeded(seed), 300.0, {}
    for day in days:
        out[day] = close
        close *= 1.0 + rng.gauss(0.0004, 0.01)
    return out


def synthetic_arm(
    name: str,
    closes: dict[date, float],
    *,
    drift: float,
    seed: int,
    noise: float = NOISE,
) -> ArmSeries:
    """Equity earning SPY at `EXPOSURE`, plus `drift` a session, plus centred noise."""
    days = sorted(closes)
    rng = seeded(seed)
    shocks = [rng.gauss(0.0, noise) for _ in days[1:]]
    centre = sum(shocks) / len(shocks)
    equity, points = START_CENTS, []
    for index, day in enumerate(days):
        points.append((day, equity, round(EXPOSURE * equity)))
        if index + 1 < len(days):
            spy_ratio = closes[days[index + 1]] / closes[day]
            step = EXPOSURE * (spy_ratio - 1.0) + drift + shocks[index] - centre
            equity = round(equity * (1.0 + step))
    return ArmSeries(name, tuple(points), dict(closes))


def five_arms(
    base_drift: float, ablation_drift: float, *, count: int = 301
) -> dict[str, ArmSeries]:
    """The five arms on one SPY walk: the sweep arms copy base-25's drift."""
    closes = spy_closes(trading_days(date(2017, 1, 3), count))
    drifts = (base_drift, base_drift, base_drift, ablation_drift, ablation_drift)
    return {
        name: synthetic_arm(name, closes, drift=drift, seed=11 + index)
        for index, (name, drift) in enumerate(zip(ARM_NAMES, drifts, strict=True))
    }


def shifted(arm: ArmSeries, name: str, drift: float) -> ArmSeries:
    """The same arm with `drift` added to every session's equity step."""
    points: list[Point] = [arm.points[0]]
    equity = arm.points[0][1]
    for previous, current in zip(arm.points, arm.points[1:], strict=False):
        equity = round(equity * (current[1] / previous[1] + drift))
        points.append((current[0], equity, round(EXPOSURE * equity)))
    return ArmSeries(name, tuple(points), dict(arm.closes))
