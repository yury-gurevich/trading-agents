"""S239 A8 / A9: the poll asks for a barrier claim only for buys with both barriers,
and a full pass touches nothing on the decision path.

Agent: forecaster
Role: prove forecast_analyst_node fires forecast_barrier once per buy that carries
      a stop and a target (with both in `features`), leaves the three existing legs
      as they were, and that a poll + handler pass writes no PM, execution or monitor
      label and sends nothing to those agents.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.forecaster.poll import forecast_analyst_node
from agents.forecaster.tests.barrier_helpers import (
    RecordingBus,
    barrier_bars,
    wire_barrier,
)
from contracts import execution, monitor, portfolio_manager
from contracts.analyst import Recommendation, RecommendationSet
from contracts.common import Explanation, Provenance
from contracts.forecaster import ForecastRequest
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from kernel.graph import Node


def _rec(
    ticker: str, action: str, stop: float | None, target: float | None
) -> Recommendation:
    return Recommendation.model_validate(
        {
            "ticker": ticker,
            "action": action,
            "confidence": 0.8,
            "technical_score": 0.7,
            "suggested_stop_pct": stop,
            "suggested_target_pct": target,
            "rationale": Explanation(summary=f"{ticker} fixture"),
        }
    )


def _analyst_run(graph: InMemoryGraphStore, *recs: Recommendation) -> Node:
    recommendation_set = RecommendationSet(
        run_id="analyst-run-s239",
        recommendations=recs,
        rejections=(),
        explanation=Explanation(summary="fixture run"),
        provenance=Provenance(run_id="analyst-run-s239", source_agent="analyst"),
    )
    return graph.merge_node(
        "AnalystRun",
        "analyst-run-s239",
        {"recommendation_set": recommendation_set.model_dump(mode="json")},
    )


_MIXED = (
    _rec("AAPL", "buy", 0.05, 0.07),
    _rec("MSFT", "buy", 0.04, None),
    _rec("NVDA", "sell", 0.05, 0.07),
    _rec("AMZN", "hold", 0.05, 0.07),
)


def test_the_poll_asks_for_a_claim_only_for_buys_with_both_barriers() -> None:
    """FORE-IN-07 / FORE-TRG-01: one forecast_barrier request, for the buy with a
    stop and a target, carrying both; the three existing legs still fire per
    recommendation."""
    graph = InMemoryGraphStore()
    bus = RecordingBus()

    forecast_analyst_node(_analyst_run(graph, *_MIXED), graph=graph, bus=bus)

    barrier = [m for m in bus.requests if m.capability == "forecast_barrier"]
    assert len(barrier) == 1
    request = ForecastRequest.model_validate(barrier[0].payload)
    assert request.subject_ref == "AAPL"
    assert request.subject_kind == "recommendation"
    assert request.features == {"stop_pct": 0.05, "target_pct": 0.07}
    others = [m.capability for m in bus.requests if m.capability != "forecast_barrier"]
    assert sorted(others) == sorted(
        ("forecast", "forecast_return", "forecast_factor") * len(_MIXED)
    )


def test_a_full_pass_never_reaches_the_decision_path() -> None:
    """FORE-NEV-02 / FORE-OUT-07: poll + handler write claims and shadow predictions
    only; no PM, execution or monitor label is written and no message goes to
    those agents."""
    bars = barrier_bars("AAPL", 760) + barrier_bars("GOOG", 760)
    bus, graph, _sink = wire_barrier(bars=bars)
    assert isinstance(graph, InMemoryGraphStore)
    run = _analyst_run(
        graph,
        _rec("AAPL", "buy", 0.05, 0.07),
        _rec("GOOG", "buy", 0.06, 0.09),
        *_MIXED[1:],
    )

    forecast_analyst_node(run, graph=graph, bus=bus)

    claims = graph.list_nodes("BarrierForecast")
    assert sorted(node.props["ticker"] for node in claims) == ["AAPL", "GOOG"]
    decision_labels = {
        *portfolio_manager.CONTRACT.owns_graph,
        *execution.CONTRACT.owns_graph,
        *monitor.CONTRACT.owns_graph,
    }
    assert decision_labels
    assert {
        label: graph.list_nodes(label) for label in decision_labels
    } == dict.fromkeys(decision_labels, ())
    assert {m.recipient for m in bus.requests} <= {"forecaster", "provider"}
