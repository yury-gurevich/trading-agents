"""Forecaster cascade-stage integration — advisory shadow predictions, never gating.

Agent: orchestration
Role: prove the forecaster stage runs in the cascade off each AnalystRun, persists
      shadow predictions for every recommendation (both legs), is idempotent on a
      second pass, and never disturbs the PM/execution trade path.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from agents.execution.paper_broker import PaperBroker
from agents.forecaster import ForecasterAgent
from agents.forecaster import poll as forecaster_poll
from agents.forecaster.barrier_fit import FakeGarchFitter
from agents.forecaster.tests.barrier_helpers import ACCEPTED, barrier_bars
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from contracts.analyst import RecommendationSet
from contracts.barrier_history import barrier_buys
from kernel import AgentMessage, InMemoryGraphStore, InProcessBus
from orchestration.local_pipeline import cascade_once
from orchestration.start import place_run_request
from orchestration.tests.helpers import ReboundingDataSource, node_count, source

if TYPE_CHECKING:
    from contracts.common import Window
    from contracts.provider import OHLCVBar


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


class _RecordingBus(InProcessBus):
    """The provider's bus, keeping the capability of every forecaster request."""

    def __init__(self) -> None:
        super().__init__()
        self.forecaster_capabilities: list[str] = []

    def request(self, message: AgentMessage) -> AgentMessage:
        if message.recipient == "forecaster":
            self.forecaster_capabilities.append(message.capability)
        return super().request(message)


def test_the_local_pipeline_still_fires_all_four_legs() -> None:
    """FORE-TRG-01: the in-process cascade fires forecast, forecast_return,
    forecast_factor and forecast_barrier; only the deployed loop narrows to one."""
    graph = InMemoryGraphStore()
    bus = _RecordingBus()
    provider = ProviderAgent(
        bus,
        graph=graph,
        source=source(),
        settings=ProviderSettings(max_staleness_days=7),
    )
    place_run_request(graph, run_id="fc4", tickers=("AAPL", "MSFT"))

    cascade_once(graph, provider_agent=provider, broker=PaperBroker())

    assert set(bus.forecaster_capabilities) == set(forecaster_poll.LOCAL_CAPABILITIES)


@dataclass
class _LongHistorySource(ReboundingDataSource):
    """The run's fixture source, plus ~3 years of bars for the barrier window only.

    A window longer than 1,000 days is the provider's BarrierHistory request; it is
    served from `long` and does not advance the fixture's rebound phase.
    """

    long: tuple[OHLCVBar, ...] = ()

    def fetch_ohlcv(
        self, tickers: tuple[str, ...], window: Window
    ) -> tuple[OHLCVBar, ...]:
        if (window.end - window.start).days < 1000:
            return super().fetch_ohlcv(tickers, window)
        return tuple(bar for bar in self.long if bar.ticker in set(tickers))


def test_the_local_pipeline_claims_from_the_provider_written_history() -> None:
    """FORE-IN-07 / FORE-OUT-07 / PROV-OUT-08 (DL-241 D10): end to end, the cascade's
    provider stage writes the run's BarrierHistory and the forecaster stage states
    one BarrierForecast per qualifying buy from it, with a fake fitter."""
    graph = InMemoryGraphStore()
    bus = InProcessBus()
    long = barrier_bars("AAPL", 800) + barrier_bars("MSFT", 800)
    base = source()
    provider = ProviderAgent(
        bus,
        graph=graph,
        source=_LongHistorySource(entry=base.entry, rebound=base.rebound, long=long),
        settings=ProviderSettings(max_staleness_days=7),
    )
    forecaster = ForecasterAgent(
        bus, graph=graph, barrier_fitter=FakeGarchFitter(ACCEPTED)
    )
    place_run_request(graph, run_id="fc-claims", tickers=("AAPL", "MSFT"))

    cascade_once(
        graph,
        provider_agent=provider,
        broker=PaperBroker(),
        forecaster_agent=forecaster,
    )

    [analyst_run] = graph.list_nodes("AnalystRun")
    recommendation_set = RecommendationSet.model_validate(
        analyst_run.props["recommendation_set"]
    )
    qualifying = sorted(rec.ticker for rec in barrier_buys(recommendation_set))
    [history] = graph.list_nodes("BarrierHistory")
    claims = graph.list_nodes("BarrierForecast")
    assert qualifying
    assert sorted(history.props["histories"]) == qualifying
    assert sorted(node.props["ticker"] for node in claims) == qualifying
    assert {node.props["history_ref"] for node in claims} == {history.key}
