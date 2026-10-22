"""EXP-015's inference and bar: IC differences, bootstrap, folds, holdout (S289).

Agent: tooling
Role: pool the folds' per-session IC differences, bootstrap every 10th session, read
      bars 1 and 2 and the shuffled-target control, then bar 3 on the holdout.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from scripts.exp015_spec import (
    BAR_FOLDS_WON,
    BAR_IC_DIFFERENCE,
    BLOCK,
    RESAMPLES,
    SEED,
    STEP_SESSIONS,
)
from scripts.replay_verdict_stats import percentile_interval, seeded, stationary_draws

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


def differences(folds: Sequence[Mapping[str, object]]) -> dict[str, float]:
    """Ensemble IC minus baseline IC on each test session both have, across folds."""
    out: dict[str, float] = {}
    for record in folds:
        ic = record["ic"]
        assert isinstance(ic, dict)
        ensemble, baseline = ic["ensemble"], ic["baseline"]
        out.update(
            {day: ensemble[day] - baseline[day] for day in ensemble if day in baseline}
        )
    return dict(sorted(out.items()))


def interval(
    diffs: Mapping[str, float], resamples: int = RESAMPLES, seed: int = SEED
) -> dict[str, object]:
    """Every STEP_SESSIONS-th difference: its mean and stationary-bootstrap 95 % CI."""
    values = list(diffs.values())[::STEP_SESSIONS]
    if not values:
        return {"sessions": 0, "mean": None, "low": None, "high": None}
    rng = seeded(seed)
    means = [
        sum(values[i] for i in stationary_draws(len(values), BLOCK, rng)) / len(values)
        for _ in range(resamples)
    ]
    low, high = percentile_interval(means)
    return {
        "sessions": len(values),
        "mean": sum(values) / len(values),
        "low": low,
        "high": high,
    }


def walk_forward_reading(
    folds: Sequence[Mapping[str, object]],
    control: Sequence[Mapping[str, object]],
    resamples: int = RESAMPLES,
) -> dict[str, object]:
    """Bars 1 and 2 on the folds, and the control: its interval must contain 0."""
    diffs = differences(folds)
    mean = sum(diffs.values()) / len(diffs) if diffs else float("nan")
    boot = interval(diffs, resamples)
    won = sum(
        1
        for record in folds
        if _fold_mean(record, "ensemble") > _fold_mean(record, "baseline")
    )
    shuffled = interval(differences(control), resamples)
    low, high = shuffled["low"], shuffled["high"]
    control_ok = (
        isinstance(low, float) and isinstance(high, float) and low <= 0.0 <= high
    )
    boot_low = boot["low"]
    bar1 = mean >= BAR_IC_DIFFERENCE and isinstance(boot_low, float) and boot_low > 0.0
    return {
        "mean_ic_difference": mean,
        "sessions": len(diffs),
        "bootstrap": boot,
        "folds_won": won,
        "folds": len(folds),
        "bar1": bool(bar1),
        "bar2": won >= BAR_FOLDS_WON,
        "control": shuffled | {"passed": bool(control_ok)},
    }


def verdict(walk: Mapping[str, object], holdout: Mapping[str, object] | None) -> str:
    """STOPPED on a failed control; PASS only when all three bars hold; else FAIL."""
    control = walk["control"]
    assert isinstance(control, dict)
    if not control["passed"]:
        return "STOPPED"
    if holdout is None:
        return "PENDING HOLDOUT"
    return "PASS" if walk["bar1"] and walk["bar2"] and holdout["bar3"] else "FAIL"


def holdout_reading(record: Mapping[str, object]) -> dict[str, object]:
    """Bar 3: the holdout's mean IC difference above 0, and the net top decile ahead."""
    diffs = differences([record])
    mean = sum(diffs.values()) / len(diffs) if diffs else float("nan")
    top = record["top_decile"]
    assert isinstance(top, dict)
    ahead = top["ensemble"]["net_return"] > top["baseline"]["net_return"]
    return {
        "mean_ic_difference": mean,
        "sessions": len(diffs),
        "net_ahead": bool(ahead),
        "bar3": bool(mean > 0.0 and ahead),
    }


def _fold_mean(record: Mapping[str, object], name: str) -> float:
    ic = record["ic"]
    assert isinstance(ic, dict)
    values = list(ic[name].values())
    return sum(values) / len(values) if values else float("-inf")
