"""Barrier test bed scoring: Brier, skill, date-resampled intervals, calibration.

Agent: tooling
Role: score stated stop-first / target-first / neither probabilities against
      outcomes the way EXP-011 and EXP-016-018 did; intervals resample whole
      decision dates, because stocks on one date move together.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Callable


def brier_losses(declared: np.ndarray, realised: np.ndarray) -> np.ndarray:
    """Per-case 3-outcome Brier: squared distance from the outcome (0 is perfect)."""
    return ((declared - realised) ** 2).sum(1)


def skill(model_losses: np.ndarray, baseline_losses: np.ndarray) -> float:
    """Brier skill against a baseline: 1 - B_model / B_baseline (1 = perfect)."""
    return float(1 - model_losses.mean() / baseline_losses.mean())


def date_draws(dates: np.ndarray, n: int, seed: int) -> list[np.ndarray]:
    """``n`` resamples of whole dates, each an array of case indices."""
    rng = np.random.default_rng(seed)
    unique = np.unique(dates)
    by_date = {u: np.where(dates == u)[0] for u in unique}
    return [
        np.concatenate([by_date[u] for u in rng.choice(unique, len(unique))])
        for _ in range(n)
    ]


def interval(
    statistic: Callable[[np.ndarray], float],
    draws: list[np.ndarray],
    level: float = 95.0,
) -> tuple[float, float]:
    """The central ``level`` % interval of ``statistic`` over the resamples."""
    values = [statistic(sample) for sample in draws]
    tail = (100 - level) / 2
    return float(np.percentile(values, tail)), float(np.percentile(values, 100 - tail))


def calibration(
    declared: np.ndarray, realised: np.ndarray, min_n: int = 100, width: float = 0.1
) -> list[tuple[float, float, int]]:
    """(mean declared, realised share, n) per bucket of at least ``min_n`` cases."""
    cells = []
    for lo in np.arange(0, 1, width):
        top = lo + width + (1e-9 if lo + width >= 1 else 0)
        sel = (declared >= lo) & (declared < top)
        if sel.sum() >= min_n:
            cells.append(
                (
                    round(float(declared[sel].mean()), 3),
                    round(float(realised[sel].mean()), 3),
                    int(sel.sum()),
                )
            )
    return cells
