"""Sprint 286 A11-A14: one history read and open-claim settlement.

Agent: forecaster
Role: count reads and prove an orphan settlement is linked without being redone.
External I/O: none.
"""

from agents.forecaster.domain.barrier_settlement import Settlement
from agents.forecaster.settlement_pass import settle_analyst_node
from agents.forecaster.settlement_store import write_settlement
from agents.forecaster.tests.barrier_helpers import (
    HISTORY_KEY,
    barrier_bars,
    barrier_message,
    seed_history,
    wire_barrier,
)
from agents.forecaster.tests.held_helpers import CountingGraph, held_record
from agents.forecaster.tests.settlement_helpers import seed_claim, seed_run
from agents.forecaster.tests.settlement_paths import AS_OF, ohlcv, path
from kernel import CollectingFaultSink, InMemoryGraphStore


def test_a_runs_claims_read_its_history_once() -> None:
    """FORE-PERF-04: three claim RPCs share exactly one BarrierHistory read."""
    graph = CountingGraph()
    tickers = ("COP", "KO", "AAPL")
    bars = tuple(bar for ticker in tickers for bar in barrier_bars(ticker, 760))
    bus, _, sink = wire_barrier(bars=bars, graph=graph)
    graph.reads.clear()

    for ticker in tickers:
        bus.request(barrier_message(ticker))

    assert graph.reads["BarrierHistory"] == 1
    assert len(graph.list_nodes("BarrierForecast")) == 3
    assert sink.faults == []


def test_a_history_the_provider_writes_later_is_read_when_it_lands() -> None:
    """FORE-PERF-04: a missing key is never cached; a later write is observed."""
    from agents.forecaster.history_cache import HistoryCache

    graph = CountingGraph()
    cache = HistoryCache()
    assert cache.read(graph, HISTORY_KEY) is None
    seed_history(graph, barrier_bars("COP", 760))

    history = cache.read(graph, HISTORY_KEY)

    assert history is not None
    assert history.requested == ("COP",)
    assert cache.read(graph, HISTORY_KEY) is history
    assert graph.reads["BarrierHistory"] == 2


def test_a_pass_lists_no_claim_and_settles_the_open_ones() -> None:
    """FORE-PERF-04 / FORE-OUT-08: settle buy and held targets without listings."""
    graph = CountingGraph()
    buy = seed_claim(graph)
    held = held_record(graph, "KO")
    target = path(events={2: (108.0, 99.0)})
    run = seed_run(graph, "open-pass", bars=ohlcv("AAPL", target) + ohlcv("KO", target))
    sink = CollectingFaultSink()
    graph.listings.clear()

    settle_analyst_node(run, graph=graph, sink=sink)

    assert graph.listings["BarrierForecast"] == 0
    assert graph.listings["BarrierSettlement"] == 0
    for claim in (buy, held):
        result = graph.get_node("BarrierSettlement", f"settlement:{claim.key}")
        assert result is not None
        assert result.props["outcome"] == "target"
    assert graph.keys_without_edge("BarrierForecast", "SETTLED_BY") == ()
    assert sink.faults == []


def test_a_settlement_written_without_its_edge_is_linked_not_redone() -> None:
    """FORE-IDM-05: an orphan stop settlement survives bars that would say target."""
    graph = CountingGraph()
    claim = seed_claim(graph)
    scratch = InMemoryGraphStore()
    source = seed_claim(scratch)
    stored = write_settlement(
        scratch,
        source,
        Settlement("stop", None, AS_OF, 100.0, 1.0),
        settling_ref="market-data:first-covering-run",
    )
    before = graph.merge_node("BarrierSettlement", stored.key, dict(stored.props))
    run = seed_run(
        graph, "orphan-pass", bars=ohlcv("AAPL", path(events={2: (108.0, 99.0)}))
    )
    sink = CollectingFaultSink()

    settle_analyst_node(run, graph=graph, sink=sink)

    assert graph.get_node("BarrierSettlement", stored.key) == before
    assert before.props["outcome"] == "stop"
    assert graph.keys_without_edge("BarrierForecast", "SETTLED_BY") == ()
    assert list(graph.descendants(claim, max_depth=1, edge_types={"SETTLED_BY"})) == [
        before
    ]
    marker = graph.get_node("BarrierSettlementPass", "settlement-pass:orphan-pass")
    assert marker is not None
    assert marker.props["settled"] == 0
    assert sink.faults == []
