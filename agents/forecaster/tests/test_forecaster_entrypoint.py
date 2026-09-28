"""Forecaster entrypoint tests: the deployed graph-pull loop (DL-241 D9).

Agent: forecaster
Role: verify the entrypoint runs a graph-pull loop that fires the barrier claim only,
      that the served bus still answers a request with a shadow-only output, and that
      a deployed forecaster's provider request fails loud (the F4 blocker).
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import agents.forecaster.entrypoint as ep
from agents.forecaster.entrypoint import build_served_bus
from agents.forecaster.poll import DEPLOYED_CAPABILITIES, forecast_analyst_node
from agents.forecaster.tests.barrier_helpers import RecordingBus
from agents.forecaster.tests.helpers import forecast_message
from contracts.analyst import Recommendation, RecommendationSet
from contracts.common import Explanation, Provenance
from contracts.forecaster import ShadowPrediction
from kernel import CollectingFaultSink, InMemoryGraphStore
from kernel.serve_loop import LocalRequestConsumer, serve_once

if TYPE_CHECKING:
    from collections.abc import Callable

    import pytest

    from kernel.graph import Node


def _analyst_run(graph: InMemoryGraphStore) -> Node:
    recs = tuple(
        Recommendation.model_validate(
            {
                "ticker": ticker,
                "action": action,
                "confidence": 0.8,
                "technical_score": 0.7,
                "suggested_stop_pct": 0.05,
                "suggested_target_pct": 0.07,
                "rationale": Explanation(summary=f"{ticker} fixture"),
            }
        )
        for ticker, action in (("AAPL", "buy"), ("GOOG", "buy"), ("NVDA", "sell"))
    )
    recommendation_set = RecommendationSet(
        run_id="analyst-run-deployed",
        recommendations=recs,
        rejections=(),
        explanation=Explanation(summary="fixture run"),
        provenance=Provenance(run_id="analyst-run-deployed", source_agent="analyst"),
    )
    return graph.merge_node(
        "AnalystRun",
        "analyst-run-deployed",
        {"recommendation_set": recommendation_set.model_dump(mode="json")},
    )


def test_main_runs_the_graph_pull_loop_with_the_barrier_leg_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FORE-TRG-01 / FORE-TRG-02: the container polls for an unconsumed AnalystRun
    and fires forecast_barrier for each buy with both barriers, and none of the
    three advisory legs."""
    graph = InMemoryGraphStore()
    _analyst_run(graph)
    bus = RecordingBus()
    seen: dict[str, object] = {}

    monkeypatch.setattr(ep, "activate_agent", lambda *args, **kwargs: None)
    monkeypatch.setattr(ep, "master_public_key_from_env", lambda: "pub")
    monkeypatch.setattr(ep, "build_graph_from_env", lambda: graph)
    monkeypatch.setattr(ep, "build_served_bus", lambda graph_arg, sink: bus)

    def fake_work_loop(
        find_pending: Callable[[], list[Node]],
        process_one: Callable[[Node], None],
        *,
        poll_interval: float,
        graph: object,
        agent: str,
        flush_faults: Callable[[], None],
    ) -> None:
        pending = find_pending()
        seen.update(pending=len(pending), poll=poll_interval, agent=agent)
        seen.update(loop_graph=graph, flush=flush_faults)
        for node in pending:
            process_one(node)
        seen["after"] = len(find_pending())

    monkeypatch.setattr(ep, "work_loop", fake_work_loop)
    monkeypatch.setenv("FORECASTER_POLL_INTERVAL", "11")

    ep.main()

    assert seen["pending"] == 1
    assert seen["after"] == 0
    assert (seen["poll"], seen["agent"], seen["loop_graph"]) == (
        11,
        "forecaster",
        graph,
    )
    assert callable(seen["flush"])
    fired = [(m.capability, m.payload["subject_ref"]) for m in bus.requests]
    assert fired == [("forecast_barrier", "AAPL"), ("forecast_barrier", "GOOG")]


def test_a_deployed_forecaster_cannot_reach_the_provider_yet() -> None:
    """FORE-FAIL-04 / DL-241 D9: a witness of the F4 blocker, not a guarantee.

    The container binds only the forecaster, and the provider serves no request,
    so the barrier leg's history request is refused: no claim, and two faults per
    buy (the refused request, then the short-history refusal) a graph sink can
    see. When a provider route exists this test must change.
    """
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    bus = build_served_bus(graph, sink)

    forecast_analyst_node(
        _analyst_run(graph), graph=graph, bus=bus, capabilities=DEPLOYED_CAPABILITIES
    )

    assert graph.list_nodes("BarrierForecast") == ()
    assert len(graph.list_nodes("ForecasterRun")) == 1
    assert [(f.error_type, f.message.split(":")[0]) for f in sink.faults] == [
        ("RuntimeError", "No handler registered for provider.get_market_data"),
        ("BarrierClaimRefusedError", "AAPL"),
        ("RuntimeError", "No handler registered for provider.get_market_data"),
        ("BarrierClaimRefusedError", "GOOG"),
    ]


def test_served_forecast_is_request_triggered_shadow_only() -> None:
    """FORE-TRG-02 / FORE-OUT-02 / FORE-NEV-02: served request writes shadow only."""
    graph = InMemoryGraphStore()
    bus = build_served_bus(graph)
    consumer = LocalRequestConsumer([forecast_message("s99-forecast")])

    served = serve_once(consumer, bus)

    assert served == 1
    assert len(consumer.replies) == 1
    prediction = ShadowPrediction.model_validate(consumer.replies[0].payload)
    assert prediction.shadow is True
    assert len(graph.list_nodes("ShadowPrediction")) == 1
    assert graph.list_nodes("OrderIntent") == ()
    assert graph.list_nodes("PMRun") == ()
    assert graph.list_nodes("CloseDecision") == ()
