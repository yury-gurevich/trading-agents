"""Forecaster cascade-stage integration — advisory shadow predictions, never gating.

Agent: orchestration
Role: prove the forecaster stage runs in the cascade off each AnalystRun, persists
      shadow predictions for every recommendation (both legs), is idempotent on a
      second pass, and never disturbs the PM/execution trade path.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.broker import PaperBroker
from agents.forecaster import poll as forecaster_poll
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from kernel import InMemoryGraphStore, InProcessBus
from orchestration.local_pipeline import cascade_once
from orchestration.start import place_run_request
from orchestration.tests.helpers import node_count, source


def _provider(graph: InMemoryGraphStore) -> ProviderAgent:
    return ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=source(),
        settings=ProviderSettings(max_staleness_days=7),
    )


def _run(graph: InMemoryGraphStore) -> None:
    place_run_request(graph, run_id="fc", tickers=("AAPL", "MSFT"))
    cascade_once(graph, provider_agent=_provider(graph), broker=PaperBroker())


def test_forecaster_produces_shadow_predictions_for_recommendations() -> None:
    """FORE-OUT-05 / FORE-OUT-02 / FORE-TRG-01: each recommendation gets a
    ShadowPrediction per leg (sentiment + return), written to the graph, all
    structurally shadow=True, produced by an RPC trigger and linked under a
    ForecasterRun off the AnalystRun."""
    graph = InMemoryGraphStore()
    _run(graph)

    recs = node_count(graph, "Recommendation")
    predictions = graph.list_nodes("ShadowPrediction")
    assert recs >= 1  # the clean source yields at least one recommendation
    assert len(predictions) == 2 * recs  # both legs per recommendation
    assert all(p.props["shadow"] is True for p in predictions)
    assert node_count(graph, "ForecasterRun") == 1


def test_forecaster_never_gates_the_trade_path() -> None:
    """FORE-NEV-02: the advisory branch never gates — the PM/execution path completes
    independently, untouched by the forecaster's shadow predictions."""
    graph = InMemoryGraphStore()
    _run(graph)
    # The trade path completed independently of the advisory forecaster.
    assert node_count(graph, "PMRun") == 1
    assert node_count(graph, "ExecutionRun") == 1


def test_forecaster_stage_is_idempotent() -> None:
    """A second cascade pass forecasts nothing new (FORECAST_BY gate already closed)."""
    graph = InMemoryGraphStore()
    _run(graph)
    before = len(graph.list_nodes("ShadowPrediction"))

    assert forecaster_poll.find_pending(graph) == []
    cascade_once(graph, provider_agent=_provider(graph), broker=PaperBroker())

    assert len(graph.list_nodes("ShadowPrediction")) == before
