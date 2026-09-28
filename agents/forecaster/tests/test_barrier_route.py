"""S239 / DL-241 D10: the deployed route from the provider's history to a claim.

Agent: forecaster
Role: prove, with two loops that share only the graph (as deployed), that the
      provider's BarrierHistory lets the forecaster state one claim per qualifying
      buy with no bus fetch, and that a failed fetch never leaves it waiting.
External I/O: none (fake source, fake fitter, in-memory graph).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.forecaster import ForecasterAgent
from agents.forecaster.barrier_fit import FakeGarchFitter
from agents.forecaster.poll import (
    DEPLOYED_CAPABILITIES,
    find_pending,
    forecast_analyst_node,
)
from agents.forecaster.tests.barrier_helpers import (
    ACCEPTED,
    RecordingBus,
    barrier_bars,
    deployed_analyst_run,
)
from agents.provider import ProviderAgent
from agents.provider.poll import find_pending_work, process_work_item
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from kernel import CollectingFaultSink, InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    import pytest


def test_a_deployed_forecaster_claims_from_the_provider_written_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FORE-IN-07 / FORE-OUT-07 / FORE-NEV-04 / PROV-OUT-08 (DL-241 D10): the route.

    Two processes share only the graph. The provider's loop writes the run's
    BarrierHistory; the forecaster, bound alone on its own bus, waits for it, then
    states one claim per qualifying buy with no fault and no provider request.
    (Until D10 this test pinned the F4 blocker: two faults per buy, no claim.)
    """
    graph = InMemoryGraphStore()
    run = deployed_analyst_run(graph)
    sink = CollectingFaultSink()
    monkeypatch.setattr(
        "agents.forecaster.agent.ArchGarchFitter", lambda: FakeGarchFitter(ACCEPTED)
    )
    bus = RecordingBus()
    ForecasterAgent(bus, graph=graph, sink=sink).bind()
    assert find_pending(graph) == []  # the forecaster waits for the history

    provider = ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=FakeDataSource(
            bars=barrier_bars("AAPL", 800) + barrier_bars("GOOG", 800)
        ),
        settings=ProviderSettings(max_staleness_days=7),
    )
    for item in find_pending_work(graph):
        process_work_item(item, agent=provider)
    [pending] = find_pending(graph)
    forecast_analyst_node(
        pending, graph=graph, bus=bus, capabilities=DEPLOYED_CAPABILITIES
    )

    claims = graph.list_nodes("BarrierForecast")
    assert sorted(node.props["ticker"] for node in claims) == ["AAPL", "GOOG"]
    assert {node.props["history_bars"] for node in claims} == {760}
    assert sink.faults == []
    assert {m.recipient for m in bus.requests} == {"forecaster"}
    assert pending.key == run.key


def test_a_failed_fetch_never_leaves_the_forecaster_waiting() -> None:
    """FORE-FAIL-04 / FORE-TRG-01 / PROV-OUT-08: bounded, the provider's source failing
    still ends the forecaster's wait. Within three passes of both loops the run is
    consumed: a failed BarrierHistory, a ForecasterRun, no claim, and one
    "provider dropped" fault per qualifying buy."""
    graph = InMemoryGraphStore()
    deployed_analyst_run(graph)
    sink = CollectingFaultSink()
    bus = RecordingBus()
    ForecasterAgent(
        bus, graph=graph, sink=sink, barrier_fitter=FakeGarchFitter(ACCEPTED)
    ).bind()
    provider = ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=FakeDataSource(fail_ohlcv=True),
        settings=ProviderSettings(max_staleness_days=7),
    )

    for _ in range(3):  # the bound: a waiting forecaster would never consume the run
        for item in find_pending_work(graph):
            process_work_item(item, agent=provider)
        for node in find_pending(graph):
            forecast_analyst_node(
                node, graph=graph, bus=bus, capabilities=DEPLOYED_CAPABILITIES
            )

    assert len(graph.list_nodes("ForecasterRun")) == 1
    [history] = graph.list_nodes("BarrierHistory")
    assert history.props["status"] == "failed"
    assert graph.list_nodes("BarrierForecast") == ()
    assert [f.message.split(";")[0] for f in sink.faults] == [
        "AAPL: provider dropped: fetch failed: source_unavailable",
        "GOOG: provider dropped: fetch failed: source_unavailable",
    ]
