"""Score EXP-022's arms: each exit arm against stops-only on shared draws (S282).

Agent: tooling
Role: every arm's blocks, the rebuild control, then each challenger's paired
      difference with its family interval, then the verdict.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scripts.exit_verdict_rule import CHALLENGERS, CHAMPION, FAMILIES, arm_name, decide
from scripts.exit_verdict_stats import (
    A_KEY,
    COMPARISONS,
    R_KEY,
    family_interval,
    resampled,
    windows,
)
from scripts.replay_verdict_score import MEAN_BLOCK, RESAMPLES, SEED
from scripts.replay_verdict_stats import arm_pairs, seeded, stationary_draws

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from scripts.replay_verdict_score import ArmSeries
    from scripts.replay_verdict_stats import Pair

CONTROL_TOLERANCE_PTS = 1e-6
Draws = tuple[list[float], list[float]]  # R, then A, one value per resample


def score_exit_arms(
    arms: Mapping[str, ArmSeries],
    *,
    resamples: int = RESAMPLES,
    mean_block: int = MEAN_BLOCK,
    seed: int = SEED,
) -> dict[str, Any]:
    """Every arm's blocks, the control, each challenger's difference, the verdict."""
    scored = {name: windows(arm) for name, arm in arms.items()}
    refusals = [
        {"arm": name, "reason": f"{gaps:.0f} gap session(s) in the scored window"}
        for name in arms
        if (gaps := scored[name]["whole"]["performance_gap_sessions"]) > 0
    ]
    result: dict[str, Any] = {
        "arms": scored,
        "bootstrap": {},
        "control": None,
        "differences": {},
        "refusals": refusals,
        "verdict": None,
    }
    if refusals:  # a gap has no pair to resample; nothing further is scored
        return result
    pairs = {name: arm_pairs(arm.points, arm.closes) for name, arm in arms.items()}
    count = len(next(iter(pairs.values())))
    if any(len(items) != count for items in pairs.values()):
        raise ValueError("arms differ in their number of session pairs")
    result["control"] = control = _control(scored, pairs, count)
    if not control["passed"]:
        refusals.append({"arm": "control", "reason": _control_reason(control)})
        return result
    draws: dict[str, Draws] = {name: ([], []) for name in arms}
    rng = seeded(seed)
    for _ in range(resamples):
        order = stationary_draws(count, mean_block, rng)  # one draw for every arm
        for name in arms:
            ret, excess = resampled(pairs[name], order)
            draws[name][0].append(ret)
            draws[name][1].append(excess)
    differences = {
        arm_name(stem, bps): _difference(scored, draws, stem, bps)
        for bps in FAMILIES
        for stem in CHALLENGERS
    }
    result["bootstrap"] = {
        "comparisons": COMPARISONS,
        "mean_block": mean_block,
        "pairs": count,
        "resamples": resamples,
        "seed": seed,
    }
    result["differences"] = differences
    result["verdict"] = decide(differences)
    return result


def _difference(
    scored: Mapping[str, Any], draws: Mapping[str, Draws], stem: str, bps: int
) -> dict[str, Any]:
    name, champion = arm_name(stem, bps), arm_name(CHAMPION, bps)
    arm, base = scored[name], scored[champion]
    paired = [
        [a - b for a, b in zip(mine, theirs, strict=True)]
        for mine, theirs in zip(draws[name], draws[champion], strict=True)
    ]
    return {
        "champion": champion,
        "point": arm["whole"][R_KEY] - base["whole"][R_KEY],
        "interval": list(family_interval(paired[0])),
        "halves": _gaps(arm["halves"], base["halves"]),
        "years": _gaps(arm["years"], base["years"]),
        "excess": {
            "point": arm["whole"][A_KEY] - base["whole"][A_KEY],
            "interval": list(family_interval(paired[1])),
        },
    }


def _gaps(rows: Sequence[dict[str, Any]], base: Sequence[Any]) -> list[float]:
    return [a[R_KEY] - b[R_KEY] for a, b in zip(rows, base, strict=True)]


def _control(
    scored: Mapping[str, Any], pairs: Mapping[str, Sequence[Pair]], count: int
) -> dict[str, Any]:
    """Each arm rebuilt in its own order must score its own whole-window R and A."""
    deviation = 0.0
    for name, items in pairs.items():
        ret, excess = resampled(items, range(count))
        whole = scored[name]["whole"]
        deviation = max(deviation, abs(ret - whole[R_KEY]), abs(excess - whole[A_KEY]))
    return {
        "max_deviation_pts": deviation,
        "passed": deviation <= CONTROL_TOLERANCE_PTS,
        "tolerance_pts": CONTROL_TOLERANCE_PTS,
    }


def _control_reason(control: Mapping[str, Any]) -> str:
    return (
        f"an arm rebuilt in its own order scored {control['max_deviation_pts']:.6g} "
        f"pts from its own R or A; it must be within {control['tolerance_pts']:g}"
    )
