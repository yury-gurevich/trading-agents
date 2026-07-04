"""Price/return IC scorecard math and graph alignment.

Agent: forecaster
Role: align persisted ShadowPrediction nodes (from forecast_return) with injected
      forward returns and compute the IC-based comparison metrics for the LightGBM
      return model.
External I/O: GraphStore reads via the injected backend.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from agents.forecaster.domain.statistics import pearson

if TYPE_CHECKING:
    from kernel import GraphStore


@dataclass(frozen=True)
class ReturnObservation:
    """One aligned complete case: a shadow prediction paired with a realized return."""

    subject_ref: str
    predicted: float  # squashed 0-1 ShadowPrediction.value
    forward_return: float


def build_return_observations(
    graph: GraphStore,
    model_id: str,
    forward_returns: dict[str, float],
) -> list[ReturnObservation]:
    """Inner-join ShadowPredictions for model_id with injected forward returns.

    Skips any subject_ref absent from either side (complete cases only).
    """
    predictions = {
        str(node.props["subject_ref"]): float(node.props.get("value", 0.5))
        for node in graph.list_nodes("ShadowPrediction")
        if node.props.get("model_id") == model_id
    }
    return [
        ReturnObservation(ref, predictions[ref], ret)
        for ref, ret in forward_returns.items()
        if ref in predictions
    ]


def return_scorecard_metrics(
    observations: list[ReturnObservation],
    *,
    neutral_prediction: float = 0.5,
    quantiles: int = 5,
) -> dict[str, float]:
    """IC + directional metrics over aligned observations; never raises.

    Empty when there are no observations. Each metric is omitted when undefined
    (fewer than two points, a constant series, or no up/down observations).
    """
    if not observations:
        return {}
    metrics: dict[str, float] = {"complete_cases": float(len(observations))}
    preds = [o.predicted for o in observations]
    rets = [o.forward_return for o in observations]
    ic = pearson(preds, rets)
    if ic is not None:
        metrics["ic"] = ic
    correct = sum(
        1 for p, r in zip(preds, rets, strict=True) if (p - neutral_prediction) * r > 0
    )
    metrics["hit_rate"] = correct / len(observations)
    up = [p for p, r in zip(preds, rets, strict=True) if r > 0]
    down = [p for p, r in zip(preds, rets, strict=True) if r <= 0]
    if up:
        metrics["mean_up_pred"] = sum(up) / len(up)
    if down:
        metrics["mean_down_pred"] = sum(down) / len(down)
    from agents.forecaster.domain.evaluation import quantile_metrics, rank_ic

    rank = rank_ic(observations)
    if rank is not None:
        metrics["rank_ic"] = rank
    metrics.update(quantile_metrics(observations, quantiles=quantiles))
    return metrics
