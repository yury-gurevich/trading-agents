"""Forecaster scorecard handlers — read-only over the graph, never promotion-eligible.

Agent: forecaster
Role: answer the scorecard, sentiment_scorecard and return_scorecard capabilities
      from the ShadowPredictions in the graph (moved out of agent.py, logic
      unchanged, by S239 / DL-241 D1, to make room for the barrier leg).
External I/O: GraphStore reads via the injected backend.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from agents.forecaster.comparison import build_observations
from agents.forecaster.domain.return_scorecard import (
    build_return_observations,
    return_scorecard_metrics,
)
from agents.forecaster.domain.scorecard import comparison_metrics
from agents.forecaster.domain.sentiment import NEUTRAL
from agents.forecaster.store import read_predictions
from contracts.forecaster import (
    ReturnScorecardRequest,
    Scorecard,
    ScorecardRequest,
    SentimentScorecardRequest,
)

if TYPE_CHECKING:
    from pydantic import BaseModel

    from kernel import GraphStore, Node


def scorecard(graph: GraphStore, request: BaseModel) -> Scorecard:
    """Summarise one model's shadow predictions; never promotion-eligible."""
    req = ScorecardRequest.model_validate(request)
    predictions = read_predictions(graph, req.model_id)
    return Scorecard(
        model_id=req.model_id,
        metrics=_scorecard_metrics(predictions),
        sample_size=len(predictions),
        fresh_as_of=datetime.now(tz=UTC),
        promotion_eligible=False,
    )


def sentiment_scorecard(graph: GraphStore, request: BaseModel) -> Scorecard:
    """Compare the sentiment scorers against injected forward returns."""
    req = SentimentScorecardRequest.model_validate(request)
    observations = build_observations(graph, req.model_id, req.forward_returns)
    return Scorecard(
        model_id=req.model_id,
        metrics=comparison_metrics(observations),
        sample_size=len(observations),
        fresh_as_of=datetime.now(tz=UTC),
        promotion_eligible=False,
    )


def return_scorecard(graph: GraphStore, request: BaseModel) -> Scorecard:
    """Compare the return model's predictions against injected forward returns."""
    req = ReturnScorecardRequest.model_validate(request)
    observations = build_return_observations(graph, req.model_id, req.forward_returns)
    return Scorecard(
        model_id=req.model_id,
        metrics=return_scorecard_metrics(observations),
        sample_size=len(observations),
        fresh_as_of=datetime.now(tz=UTC),
        promotion_eligible=False,
    )


def _scorecard_metrics(predictions: tuple[Node, ...]) -> dict[str, float]:
    if not predictions:
        return {"mean_value": NEUTRAL, "mean_confidence": 0.0}
    values = [float(node.props.get("value", NEUTRAL)) for node in predictions]
    confidences = [float(node.props.get("confidence", 0.0)) for node in predictions]
    return {
        "mean_value": sum(values) / len(values),
        "mean_confidence": sum(confidences) / len(confidences),
    }
