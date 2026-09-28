"""Forecaster graph-poll work source — advisory shadow predictions per AnalystRun.

Agent: forecaster
Role: find AnalystRun nodes not yet forecast and, for each recommendation, request
      the chosen advisory legs from the forecaster over the bus: shadow sentiment,
      return and factor predictions, and a barrier claim for each buy carrying a stop
      and a target (FORE-TRG-01/02: an unconsumed AnalystRun is the trigger, never a
      timer; FORE-NEV: shadow, never gates). The caller names the legs (DL-241 D9).
      The predictions are a side branch off AnalystRun — they never touch the
      PM/execution path, so a missing or slow forecaster cannot block a trade.
External I/O: none directly (the bus carries the forecast RPCs; provider owns the I/O).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.analyst import RecommendationSet
from contracts.barrier_history import (
    BARRIER_HISTORY_LABEL,
    barrier_buys,
    barrier_history_key,
)
from contracts.forecaster import ForecastRequest
from kernel import AgentMessage

if TYPE_CHECKING:
    from contracts.analyst import Recommendation
    from kernel import GraphStore, MessageBus, Node

ANALYST_RUN_LABEL = "AnalystRun"
FORECASTER_RUN_LABEL = "ForecasterRun"
FORECAST_EDGE = "FORECAST_BY"
#: Advisory legs: FinBERT sentiment, LightGBM return, and optional factor shadow.
ADVISORY_CAPABILITIES = ("forecast", "forecast_return", "forecast_factor")
#: The barrier claim (S239): only for a buy that carries a stop and a target.
BARRIER_CAPABILITY = "forecast_barrier"
#: The in-process pipeline (`orchestration/local_pipeline.py`) fires every leg.
LOCAL_CAPABILITIES = (*ADVISORY_CAPABILITIES, BARRIER_CAPABILITY)
#: The deployed loop fires the barrier claim only (FORE-TRG-01, DL-241 D9): the three
#: advisory legs have never run in the fleet and their cost there is unmeasured.
DEPLOYED_CAPABILITIES = (BARRIER_CAPABILITY,)


def find_pending(graph: GraphStore) -> list[Node]:
    """Return AnalystRun nodes with no ForecasterRun that are ready to forecast.

    A run holding a buy with both barriers waits until the provider has written its
    BarrierHistory (DL-241 D10); a run with no such buy never waits.
    """
    pending: list[Node] = []
    for node in graph.list_nodes(ANALYST_RUN_LABEL):
        done = list(graph.descendants(node, max_depth=1, edge_types={FORECAST_EDGE}))
        if not done and _history_ready(graph, node):
            pending.append(node)
    return pending


def _history_ready(graph: GraphStore, node: Node) -> bool:
    raw = node.props.get("recommendation_set")
    if raw is None:  # no recommendations to wait for; processing reports the gap
        return True
    if not barrier_buys(RecommendationSet.model_validate(raw)):
        return True
    return (
        graph.get_node(BARRIER_HISTORY_LABEL, barrier_history_key(node.key)) is not None
    )


def forecast_analyst_node(
    node: Node,
    *,
    graph: GraphStore,
    bus: MessageBus,
    capabilities: tuple[str, ...],
) -> None:
    """Request the named advisory legs for each recommendation, then mark the run.

    ``capabilities`` is the set of legs this caller fires: ``LOCAL_CAPABILITIES`` or
    ``DEPLOYED_CAPABILITIES``; a name outside ``LOCAL_CAPABILITIES`` is refused before
    any request. The forecaster's handlers persist their own outputs; this stage only
    triggers them (RPC) and writes a ``ForecasterRun`` marker linked back to the
    AnalystRun so a second pass is idempotent. Nothing here gates the PM.
    """
    unknown = sorted(set(capabilities) - set(LOCAL_CAPABILITIES))
    if unknown:
        raise ValueError(f"unknown forecaster capabilities: {unknown}")
    recommendation_set = RecommendationSet.model_validate(
        node.props["recommendation_set"]
    )
    advisory = [name for name in ADVISORY_CAPABILITIES if name in capabilities]
    barrier = {id(rec) for rec in barrier_buys(recommendation_set)}
    for recommendation in recommendation_set.recommendations:
        for capability in advisory:
            _request_forecast(bus, capability, recommendation.ticker)
        if id(recommendation) in barrier and BARRIER_CAPABILITY in capabilities:
            _request_forecast(
                bus,
                BARRIER_CAPABILITY,
                recommendation.ticker,
                features=_barrier_features(recommendation),
                history_ref=barrier_history_key(node.key),
            )
    forecaster_run = graph.merge_node(
        FORECASTER_RUN_LABEL,
        node.key,
        {
            "recommendation_count": len(recommendation_set.recommendations),
            "source_analyst_run_id": node.key,
        },
    )
    graph.add_edge(node, forecaster_run, FORECAST_EDGE)


def _barrier_features(recommendation: Recommendation) -> dict[str, float]:
    """A qualifying buy's stop and target as request features."""
    return {
        "stop_pct": float(recommendation.suggested_stop_pct or 0.0),
        "target_pct": float(recommendation.suggested_target_pct or 0.0),
    }


def _request_forecast(
    bus: MessageBus,
    capability: str,
    ticker: str,
    *,
    features: dict[str, float] | None = None,
    history_ref: str | None = None,
) -> None:
    """Fire one advisory forecast RPC; the forecaster persists the shadow output."""
    bus.request(
        AgentMessage(
            sender="orchestration",
            recipient="forecaster",
            message_type="request",
            capability=capability,
            payload=ForecastRequest(
                subject_kind="recommendation",
                subject_ref=ticker,
                features=features or {},
                history_ref=history_ref,
            ).model_dump(mode="json"),
        )
    )
