"""Forecaster graph-poll work source — advisory shadow predictions per AnalystRun.

Agent: forecaster
Role: find AnalystRun nodes not yet forecast and, for each recommendation, request an
      advisory shadow sentiment + return prediction from the forecaster over the bus
      (FORE-TRG-01: RPC-triggered, never self-triggers; FORE-NEV: shadow, never gates).
      The predictions are a side branch off AnalystRun — they never touch the
      PM/execution path, so a missing or slow forecaster cannot block a trade.
External I/O: none directly (the bus carries the forecast RPCs; provider owns the I/O).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.analyst import RecommendationSet
from contracts.forecaster import ForecastRequest
from kernel import AgentMessage

if TYPE_CHECKING:
    from kernel import GraphStore, MessageBus, Node

ANALYST_RUN_LABEL = "AnalystRun"
FORECASTER_RUN_LABEL = "ForecasterRun"
FORECAST_EDGE = "FORECAST_BY"
#: Both advisory legs: FinBERT sentiment + the LightGBM return predictor.
_CAPABILITIES = ("forecast", "forecast_return")


def find_pending(graph: GraphStore) -> list[Node]:
    """Return AnalystRun nodes with no downstream ForecasterRun (unprocessed work)."""
    pending: list[Node] = []
    for node in graph.list_nodes(ANALYST_RUN_LABEL):
        done = list(graph.descendants(node, max_depth=1, edge_types={FORECAST_EDGE}))
        if not done:
            pending.append(node)
    return pending


def forecast_analyst_node(node: Node, *, graph: GraphStore, bus: MessageBus) -> None:
    """Request advisory shadow predictions for each recommendation, then mark the run.

    The forecaster's handlers persist each ``ShadowPrediction`` themselves; this stage
    only triggers them (RPC) and writes a ``ForecasterRun`` marker linked back to the
    AnalystRun so a second pass is idempotent. Nothing here gates the PM.
    """
    recommendation_set = RecommendationSet.model_validate(
        node.props["recommendation_set"]
    )
    for recommendation in recommendation_set.recommendations:
        for capability in _CAPABILITIES:
            _request_forecast(bus, capability, recommendation.ticker)
    forecaster_run = graph.merge_node(
        FORECASTER_RUN_LABEL,
        node.key,
        {
            "recommendation_count": len(recommendation_set.recommendations),
            "source_analyst_run_id": node.key,
        },
    )
    graph.add_edge(node, forecaster_run, FORECAST_EDGE)


def _request_forecast(bus: MessageBus, capability: str, ticker: str) -> None:
    """Fire one advisory forecast RPC; the forecaster persists the shadow output."""
    bus.request(
        AgentMessage(
            sender="orchestration",
            recipient="forecaster",
            message_type="request",
            capability=capability,
            payload=ForecastRequest(
                subject_kind="recommendation", subject_ref=ticker, features={}
            ).model_dump(mode="json"),
        )
    )
