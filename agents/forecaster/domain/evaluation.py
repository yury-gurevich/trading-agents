"""Pure evaluation battery math for return-model signal evidence.

Agent: forecaster
Role: compute rank IC, quantile returns, cross-sectional IC series, and signal
      stability over return observations.
External I/O: none.
"""

from __future__ import annotations

from itertools import pairwise
from typing import TYPE_CHECKING

from agents.forecaster.domain.statistics import pearson, spearman, std

if TYPE_CHECKING:
    from agents.forecaster.domain.return_scorecard import ReturnObservation

DEFAULT_QUANTILES = 5


def rank_ic(observations: list[ReturnObservation]) -> float | None:
    """Return Spearman IC over prediction scores and realized forward returns."""
    return spearman(
        [obs.predicted for obs in observations],
        [obs.forward_return for obs in observations],
    )


def quantile_metrics(
    observations: list[ReturnObservation],
    *,
    quantiles: int = DEFAULT_QUANTILES,
) -> dict[str, float]:
    """Return deterministic quantile mean returns and top-bottom spread."""
    if quantiles < 2 or len(observations) < 2 * quantiles:
        return {}
    sorted_obs = sorted(observations, key=lambda obs: (obs.predicted, obs.subject_ref))
    base_size = len(sorted_obs) // quantiles
    larger_tail_buckets = len(sorted_obs) % quantiles
    small_buckets = quantiles - larger_tail_buckets
    means: list[float] = []
    start = 0
    for bucket_index in range(quantiles):
        size = base_size + (1 if bucket_index >= small_buckets else 0)
        bucket = sorted_obs[start : start + size]
        means.append(sum(obs.forward_return for obs in bucket) / len(bucket))
        start += size

    metrics = {f"q{index}_mean_ret": mean for index, mean in enumerate(means, start=1)}
    metrics["top_bottom_spread"] = means[-1] - means[0]
    monotone_pairs = sum(
        1 for current, next_mean in pairwise(means) if next_mean >= current
    )
    metrics["monotonic_fraction"] = monotone_pairs / (quantiles - 1)
    return metrics


def ic_series_metrics(
    by_period: dict[str, list[ReturnObservation]],
) -> dict[str, float]:
    """Summarize per-period cross-sectional Pearson IC values."""
    ics = [
        ic
        for observations in by_period.values()
        if (
            ic := pearson(
                [obs.predicted for obs in observations],
                [obs.forward_return for obs in observations],
            )
        )
        is not None
    ]
    if not ics:
        return {}
    ic_mean = sum(ics) / len(ics)
    ic_std = std(ics)
    metrics = {
        "ic_mean": ic_mean,
        "ic_std": ic_std,
        "ic_periods": float(len(ics)),
    }
    if ic_std != 0.0:
        metrics["ic_ir"] = ic_mean / ic_std
    return metrics


def rank_autocorrelation(
    prev: dict[str, float],
    curr: dict[str, float],
) -> float | None:
    """Return Spearman rank autocorrelation over shared subject refs."""
    refs = sorted(prev.keys() & curr.keys())
    if len(refs) < 2:
        return None
    return spearman([prev[ref] for ref in refs], [curr[ref] for ref in refs])
