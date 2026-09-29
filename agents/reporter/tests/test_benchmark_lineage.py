"""The reporter's benchmark is its own run's MarketData (S242 A6/A7, DL-246).

Agent: reporter
Role: prove a run benchmarks on its own MarketData by lineage, reading no other run's,
      and that no benchmark there is the no-benchmark path.
External I/O: none (in-memory graph).
"""

from __future__ import annotations

from datetime import date

from agents.reporter.performance_inputs import read_performance_inputs
from agents.reporter.result import build_snapshot
from agents.reporter.settings import ReporterSettings
from agents.reporter.tests.benchmark_lineage import MarketDataSpy, link_run_market
from kernel import CollectingFaultSink

_INCEPTION = date(2026, 8, 10)
_AS_OF = "2026-08-12T23:50:00+00:00"


def _bars(*closes: float) -> list[dict[str, object]]:
    days = ("2026-08-10", "2026-08-11", "2026-08-12")
    return [
        {"ticker": "SPY", "bar_date": day, "close": close}
        for day, close in zip(days, closes, strict=False)
    ]


def _graph(own_benchmark: list[dict[str, object]]) -> MarketDataSpy:
    """Two runs' MarketData: the report's own (earlier) and a later run's."""
    graph = MarketDataSpy()
    graph.merge_node("PMRun", "pm-run-own", {"created_at": _AS_OF})
    own = graph.merge_node(
        "MarketData",
        "market-data:own",
        {"window_end": "2026-08-11", "snapshot": {"benchmark": own_benchmark}},
    )
    other = graph.merge_node(
        "MarketData",
        "market-data:other",
        {"window_end": "2026-08-12", "snapshot": {"benchmark": _bars(200, 202, 204)}},
    )
    link_run_market(graph, "pm-run-own", own, run="own")
    link_run_market(graph, "pm-run-other", other, run="other")
    for day, equity in (("2026-08-10", 1_000_000), ("2026-08-11", 1_010_000)):
        graph.merge_node(
            "BrokerPositionSnapshot",
            f"snapshot:{day}",
            {
                "status": "fresh",
                "account_status": "fresh",
                "created_at": f"{day}T22:30:00+00:00",
                "account_equity_cents": equity,
                "holdings": [{"market_value_cents": 500_000}],
            },
        )
    graph.read.clear()
    return graph


def test_a_run_benchmarks_on_its_own_market_data_by_lineage() -> None:
    """RPT-OUT-07 / RPT-IDM-03 (DL-246): the series is the run's own MarketData's,
    found through PMRun -> AnalystRun <- ScanRun -> MarketData; the later run's
    node is never read, and no MarketData is listed."""
    graph = _graph(_bars(100, 101))
    pm_run = graph.get_node("PMRun", "pm-run-own")
    assert pm_run is not None

    inputs = read_performance_inputs(graph, pm_run, inception=_INCEPTION)

    assert inputs.benchmark_closes == {
        date(2026, 8, 10): 100.0,
        date(2026, 8, 11): 101.0,
    }
    assert inputs.benchmark_ticker == "SPY"
    assert graph.read == ["market-data:own"]


def test_no_benchmark_on_the_runs_own_node_is_the_no_benchmark_path() -> None:
    """RPT-OUT-07 / RPT-NEV-03 (DL-246): the run's MarketData has no benchmark, so
    the snapshot names a missing benchmark; another run's series is never used."""
    graph = _graph([])
    sink = CollectingFaultSink()
    settings = ReporterSettings(performance_inception=_INCEPTION)

    snapshot = build_snapshot(graph, "pm-run-own", settings=settings, sink=sink)

    assert snapshot.performance_metrics["performance_sessions"] == 0.0
    assert "missing benchmark" in snapshot.headline.summary
    assert "market-data:other" not in graph.read
    assert sink.faults == []
