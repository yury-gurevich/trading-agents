"""S241: a pass that meets what it cannot read records a fault and still completes.

Agent: forecaster
Role: prove a claim the pass cannot read faults and stays open while the others
      settle, an unreadable MarketData faults while the 45-day rule still runs, and
      a run with no readable creation stamp is dated today (DL-243 D3).
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from agents.forecaster.settlement_pass import settle_analyst_node
from agents.forecaster.tests.settlement_helpers import seed_claim, seed_run
from agents.forecaster.tests.settlement_paths import AS_OF, ohlcv, path
from kernel import CollectingFaultSink, InMemoryGraphStore


def test_a_claim_the_pass_cannot_read_faults_and_stays_open() -> None:
    """FORE-FAIL-05: a claim whose as_of cannot be read records a fault naming the
    pass and stays open; the readable claim beside it settles, and the pass is
    marked done."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    seed_claim(graph)
    graph.merge_node(
        "BarrierForecast",
        "barrier-garch-v1:BAD:2026-09-28",
        {"ticker": "BAD", "as_of": "not-a-date", "model_id": "barrier-garch-v1"},
    )
    run = seed_run(graph, "run-a", bars=ohlcv("AAPL", path(events={2: (108.0, 99.0)})))

    settle_analyst_node(run, graph=graph, sink=sink)

    [settlement] = graph.list_nodes("BarrierSettlement")
    assert settlement.props["ticker"] == "AAPL"
    [fault] = sink.faults
    assert fault.source_module == "agents.forecaster.settlement_pass"
    assert fault.error_type == "ValueError"
    marker = graph.get_node("BarrierSettlementPass", "settlement-pass:run-a")
    assert marker is not None
    assert (marker.props["settled"], marker.props["open"]) == (1, 1)


def test_an_unreadable_market_data_faults_and_the_age_rule_still_runs() -> None:
    """FORE-FAIL-05: the run's MarketData cannot be read (a fault, no bars); a
    claim 50 days old is still voided no_settling_bars on that pass, and a young
    one stays open."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    seed_claim(graph)
    seed_claim(graph, ticker="MSFT", as_of=AS_OF + timedelta(days=40))
    run = seed_run(
        graph, "run-corrupt", lineage=False, created=AS_OF + timedelta(days=50)
    )
    market = graph.merge_node(
        "MarketData", "market-data:run-corrupt", {"snapshot": {"bars": "garbage"}}
    )
    scan = graph.merge_node("ScanRun", "scan-run-corrupt", {})
    graph.add_edge(scan, market, "DERIVED_FROM")
    graph.add_edge(scan, run, "ANALYZED_BY")

    settle_analyst_node(run, graph=graph, sink=sink)

    [fault] = sink.faults
    assert fault.source_module == "agents.forecaster.settling_bars"
    [void] = graph.list_nodes("BarrierSettlement")
    assert (void.props["ticker"], void.props["void_reason"]) == (
        "AAPL",
        "no_settling_bars",
    )
    assert void.props["settled_on"] == (AS_OF + timedelta(days=50)).isoformat()
    marker = graph.get_node("BarrierSettlementPass", "settlement-pass:run-corrupt")
    assert marker is not None
    assert marker.props["settling_ref"] == "market-data:run-corrupt"
    assert (marker.props["voided"], marker.props["open"]) == (1, 1)


def test_a_run_without_a_readable_stamp_is_dated_today() -> None:
    """DL-243 D3: a hand-built run with no created_at is dated by today's UTC date,
    and the date the pass used is on its marker."""
    graph = InMemoryGraphStore()
    run = graph.merge_node("AnalystRun", "run-undated", {})
    before = datetime.now(tz=UTC).date()

    settle_analyst_node(run, graph=graph)

    after = datetime.now(tz=UTC).date()
    marker = graph.get_node("BarrierSettlementPass", "settlement-pass:run-undated")
    assert marker is not None
    assert marker.props["pass_date"] in {before.isoformat(), after.isoformat()}
    assert marker.props["settling_ref"] is None
