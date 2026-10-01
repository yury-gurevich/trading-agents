"""Score EXP-014's arms: windows, one shared bootstrap, control and verdict (S250).

Agent: tooling
Role: every arm's statistic and interval via calculate_performance, then decide.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from scripts.replay_verdict_rule import ABLATION_ARMS, BASE_ARM, decide
from scripts.replay_verdict_stats import (
    annualised_excess,
    arm_pairs,
    percentile_interval,
    performance,
    rebuild,
    replica_pairs,
    seeded,
    stationary_draws,
)
from scripts.replay_verdict_windows import Window, half_windows, year_windows

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from datetime import date

    from scripts.replay_verdict_stats import Pair, Point

# Appendix P's interval: stationary bootstrap, mean block 20, 10,000 draws, seed 0.
RESAMPLES = 10_000
MEAN_BLOCK = 20
SEED = 0
CONTROL_TOLERANCE_PTS = 1e-6  # DL-258 D5: the rebuild rounds about 1e-14 a step


@dataclass(frozen=True)
class ArmSeries:
    """One arm's daily points (date, equity cents, invested cents) and SPY closes."""

    name: str
    points: tuple[Point, ...]
    closes: dict[date, float]


def score_arms(
    arms: Mapping[str, ArmSeries],
    *,
    resamples: int = RESAMPLES,
    mean_block: int = MEAN_BLOCK,
    seed: int = SEED,
    replica: Callable[[Sequence[Pair]], Sequence[Pair]] = replica_pairs,
) -> dict[str, Any]:
    """Each arm's windows and interval, paired differences, control and verdict."""
    scored = {name: _windows(arm) for name, arm in arms.items()}
    refusals = [
        {"arm": name, "reason": f"{gaps:.0f} gap session(s) in the scored window"}
        for name in arms
        if (gaps := scored[name]["whole"]["performance_gap_sessions"]) > 0
    ]
    result: dict[str, Any] = {"arms": scored, "refusals": refusals, "verdict": None}
    if refusals:  # a gap has no pair to resample; nothing further is scored
        return {**result, "bootstrap": {}, "control": None, "differences": {}}
    pairs = {name: arm_pairs(arm.points, arm.closes) for name, arm in arms.items()}
    count = len(pairs[BASE_ARM])
    if any(len(items) != count for items in pairs.values()):
        raise ValueError("arms differ in their number of session pairs")
    control_pairs = replica(pairs[BASE_ARM])
    draws: dict[str, list[float]] = {name: [] for name in arms}
    control_draws: list[float] = []
    rng = seeded(seed)
    for _ in range(resamples):
        order = stationary_draws(count, mean_block, rng)  # one draw for every arm
        for name in arms:
            draws[name].append(_resampled(pairs[name], order))
        control_draws.append(_resampled(control_pairs, order))
    intervals = {name: percentile_interval(values) for name, values in draws.items()}
    for name, interval in intervals.items():
        scored[name]["interval"] = list(interval)
    differences = {
        arm: _difference(scored, draws, arm) for arm in ABLATION_ARMS if arm in arms
    }
    control = _control(control_pairs, control_draws, count)
    if not control["passed"]:
        refusals.append({"arm": "control", "reason": _control_reason(control)})
    else:
        paired = {arm: _bounds(item["interval"]) for arm, item in differences.items()}
        result["verdict"] = decide(intervals, paired)
    return {
        **result,
        "bootstrap": {
            "mean_block": mean_block,
            "pairs": count,
            "resamples": resamples,
            "seed": seed,
        },
        "control": control,
        "differences": differences,
    }


def _bounds(interval: list[float]) -> tuple[float, float]:
    return interval[0], interval[1]


def _windows(arm: ArmSeries) -> dict[str, Any]:
    whole = Window("whole", False, tuple(sorted(arm.points)))
    years = [_row(window, arm.closes) for window in year_windows(arm.points)]
    return {
        "whole": _row(whole, arm.closes),
        "years": years,
        "years_with_positive_excess": sum(
            1 for row in years if row["annualised_excess_pts"] > 0
        ),
        "halves": [_row(window, arm.closes) for window in half_windows(arm.points)],
    }


def _row(window: Window, closes: Mapping[date, float]) -> dict[str, Any]:
    metrics = performance(window.points, closes)
    return {
        "label": window.label,
        "first": window.points[0][0].isoformat(),
        "last": window.points[-1][0].isoformat(),
        "partial": window.partial,
        **metrics,
        "annualised_excess_pts": annualised_excess(metrics),
    }


def _resampled(pairs: Sequence[Pair], order: Sequence[int]) -> float:
    points, closes = rebuild(pairs, order)
    return annualised_excess(performance(points, closes))


def _difference(
    scored: dict[str, Any], draws: dict[str, list[float]], arm: str
) -> dict[str, Any]:
    point = (
        scored[arm]["whole"]["annualised_excess_pts"]
        - scored[BASE_ARM]["whole"]["annualised_excess_pts"]
    )
    paired = [a - b for a, b in zip(draws[arm], draws[BASE_ARM], strict=True)]
    return {"point": point, "interval": list(percentile_interval(paired))}


def _control(pairs: Sequence[Pair], draws: list[float], count: int) -> dict[str, Any]:
    whole = _resampled(pairs, range(count))
    low, high = percentile_interval(draws)
    passed = all(abs(value) <= CONTROL_TOLERANCE_PTS for value in (whole, low, high))
    return {
        "annualised_excess_pts": whole,
        "interval": [low, high],
        "passed": passed,
        "tolerance_pts": CONTROL_TOLERANCE_PTS,
    }


def _control_reason(control: dict[str, Any]) -> str:
    low, high = control["interval"]
    return (
        f"the replica of {BASE_ARM} earning SPY at its exposure scored "
        f"A = {control['annualised_excess_pts']:.6f}, "
        f"interval [{low:.6f}, {high:.6f}]; "
        f"it must be 0 within {CONTROL_TOLERANCE_PTS:g}"
    )
