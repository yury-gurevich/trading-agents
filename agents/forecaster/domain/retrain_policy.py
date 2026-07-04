"""Pure rolling-retrain and champion-comparison policy.

Agent: forecaster
Role: decide when return-model evidence warrants retraining and whether a
      challenger should replace the incumbent.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrainDecision:
    """A deterministic IC-decay verdict."""

    retrain: bool
    reason: str
    recent: float | None
    reference: float | None


@dataclass(frozen=True)
class CompareVerdict:
    """A deterministic champion-vs-challenger verdict."""

    swap: bool
    reason: str
    primary_delta: float | None
    secondary_delta: float | None


def should_retrain(
    recent: dict[str, float],
    reference: dict[str, float],
    *,
    metric_key: str = "ic_ir",
    trigger_fraction: float,
    min_cases: float,
) -> RetrainDecision:
    """Return whether recent evidence has decayed enough to recommend retrain."""
    if recent.get("complete_cases", 0.0) < min_cases:
        return RetrainDecision(False, "insufficient recent cases", None, None)
    recent_value = recent.get(metric_key)
    reference_value = reference.get(metric_key)
    if recent_value is None or reference_value is None:
        return RetrainDecision(False, "metric undefined", recent_value, reference_value)
    if reference_value <= 0.0:
        return RetrainDecision(
            True, "reference non-positive", recent_value, reference_value
        )
    threshold = trigger_fraction * reference_value
    retrain = recent_value < threshold
    relation = "<" if retrain else ">="
    reason = f"recent {recent_value:.4f} {relation} trigger {threshold:.4f}"
    return RetrainDecision(retrain, reason, recent_value, reference_value)


def compare_models(
    incumbent: dict[str, float],
    challenger: dict[str, float],
    *,
    primary: str = "rank_ic",
    secondary: str = "ic_ir",
) -> CompareVerdict:
    """Return whether a challenger beats the incumbent on both metrics."""
    challenger_primary = challenger.get(primary)
    challenger_secondary = challenger.get(secondary)
    if challenger_primary is None or challenger_secondary is None:
        return CompareVerdict(False, "challenger metric undefined", None, None)
    incumbent_primary = incumbent.get(primary)
    incumbent_secondary = incumbent.get(secondary)
    if incumbent_primary is None or incumbent_secondary is None:
        return CompareVerdict(True, "incumbent metric undefined", None, None)
    primary_delta = challenger_primary - incumbent_primary
    secondary_delta = challenger_secondary - incumbent_secondary
    swap = primary_delta >= 0.0 and secondary_delta >= 0.0
    reason = "challenger wins both metrics" if swap else "challenger did not win both"
    return CompareVerdict(swap, reason, primary_delta, secondary_delta)
