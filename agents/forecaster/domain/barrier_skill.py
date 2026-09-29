"""Barrier ledger scoring, pure: EXP-018's Brier, skill and date bootstrap.

Agent: forecaster
Role: score settled claims as EXP-018's `exp018_score.py` `run()` scored its cases
      (copied: per-case three-class Brier, skill = 1 - model / climatology, and a
      95 % interval from 1,000 resamples of whole dates with a fixed seed), against
      EXP-018's fixed climatology: pre-registered, never re-estimated from the
      ledger it scores (S241, DL-243). It reports; it decides nothing.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from agents.forecaster.domain.barrier_settlement import OUTCOMES

if TYPE_CHECKING:
    from collections.abc import Sequence

    from numpy.typing import NDArray

#: EXP-018's primary-set realised shares (Appendix R): stop, target, neither.
CLIMATOLOGY = (0.287, 0.477, 0.236)
#: EXP-018's interval: 1,000 resamples of whole dates, seed 20260929 (its `run()`).
BOOTSTRAP_DRAWS = 1000
BOOTSTRAP_SEED = 20260929


@dataclass(frozen=True)
class ScoredCase:
    """One settled claim as the scorer reads it."""

    as_of: str
    outcome: int
    """Index into ``OUTCOMES``."""
    declared: tuple[float, float, float]
    brier: float


def ledger_scores(cases: Sequence[ScoredCase]) -> dict[str, float]:
    """Shares, mean declared, Brier, skill and the interval; empty with no case.

    ``cases`` in a fixed order (the caller sorts): the bootstrap resamples them.
    """
    if not cases:
        return {}
    realised = np.eye(3)[[case.outcome for case in cases]]
    declared = np.array([case.declared for case in cases])
    model = np.array([case.brier for case in cases])
    climatology = ((np.array(CLIMATOLOGY) - realised) ** 2).sum(1)
    brier_model, brier_climatology = model.mean(), climatology.mean()
    scores: dict[str, float] = {}
    for index, name in enumerate(OUTCOMES):
        scores[f"realised_{name}"] = float(realised.mean(0)[index])
        scores[f"declared_{name}"] = float(declared.mean(0)[index])
    scores["brier_model"] = float(brier_model)
    scores["brier_climatology"] = float(brier_climatology)
    scores["skill"] = float(1 - brier_model / brier_climatology)
    interval = _date_interval(
        model, climatology, np.array([case.as_of for case in cases])
    )
    if interval is not None:
        scores["skill_lo"], scores["skill_hi"] = interval
    return scores


def _date_interval(
    model: NDArray[np.float64],
    climatology: NDArray[np.float64],
    dates: NDArray[np.str_],
) -> tuple[float, float] | None:
    """EXP-018's 95 % skill interval over resampled dates; None under two dates."""
    udates = np.unique(dates)
    if len(udates) < 2:
        return None
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    by_date = {u: np.where(dates == u)[0] for u in udates}
    draws = [
        np.concatenate([by_date[u] for u in rng.choice(udates, len(udates))])
        for _ in range(BOOTSTRAP_DRAWS)
    ]
    sk = [1 - model[s].mean() / climatology[s].mean() for s in draws]
    return float(np.percentile(sk, 2.5)), float(np.percentile(sk, 97.5))
