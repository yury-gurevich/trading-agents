"""Barrier return scores, pure: whether the returns the claims stated came true.

Agent: forecaster
Role: score the settled claims that stated their return figures (DL-312): the mean
      declared expected return against the mean return realised by the outcome's
      rule, their difference with a 95 % interval from EXP-018's date bootstrap
      (1,000 resamples of whole dates, its fixed seed, as the skill's), and the share
      of tenth closes below their declared 5th percentile (near 0.05 when the tail
      is calibrated). It reports; it decides nothing.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from agents.forecaster.domain.barrier_skill import BOOTSTRAP_DRAWS, BOOTSTRAP_SEED

if TYPE_CHECKING:
    from collections.abc import Sequence

    from numpy.typing import NDArray


@dataclass(frozen=True)
class ReturnCase:
    """One settled claim's stated and realised return figures."""

    as_of: str
    declared: float
    """The claim's ``expected_return``."""
    realised: float
    """The settlement's ``realised_return``."""
    close_p05: float
    """The claim's ``close_return_p05``."""
    close_return: float
    """The settlement's ``close_return``."""


def return_scores(cases: Sequence[ReturnCase]) -> dict[str, float]:
    """Count, means, the bias and its interval, the tail's share; empty with no case.

    ``cases`` in a fixed order (the caller sorts): the bootstrap resamples them.
    """
    if not cases:
        return {}
    declared = np.array([case.declared for case in cases])
    realised = np.array([case.realised for case in cases])
    below = np.array([case.close_return < case.close_p05 for case in cases])
    scores = {
        "return_settled": float(len(cases)),
        "declared_return": float(declared.mean()),
        "realised_return": float(realised.mean()),
        "return_bias": float(realised.mean() - declared.mean()),
        "close_below_p05": float(below.mean()),
    }
    interval = _bias_interval(
        realised - declared, np.array([case.as_of for case in cases])
    )
    if interval is not None:
        scores["return_bias_lo"], scores["return_bias_hi"] = interval
    return scores


def _bias_interval(
    gap: NDArray[np.float64], dates: NDArray[np.str_]
) -> tuple[float, float] | None:
    """The bias's 95 % interval over resampled dates; None under two dates."""
    udates = np.unique(dates)
    if len(udates) < 2:
        return None
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    by_date = {u: np.where(dates == u)[0] for u in udates}
    draws = [
        np.concatenate([by_date[u] for u in rng.choice(udates, len(udates))])
        for _ in range(BOOTSTRAP_DRAWS)
    ]
    means = [gap[s].mean() for s in draws]
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))
