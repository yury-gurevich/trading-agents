"""Every broken benchmark lineage is the no-benchmark path (S242 A7, DL-246).

Agent: reporter
Role: prove every broken lineage hop and unusable own node gives no benchmark.
External I/O: none (in-memory graph).
"""

from __future__ import annotations

from datetime import date

import pytest

from agents.reporter.benchmark_input import run_benchmark
from agents.reporter.tests.benchmark_lineage import link_run_market
from kernel import InMemoryGraphStore

_AS_OF = date(2026, 8, 12)
_BARS = ({"ticker": "SPY", "bar_date": "2026-08-12", "close": 101.0},)


def _linked(props: dict[str, object]) -> InMemoryGraphStore:
    graph = InMemoryGraphStore()
    graph.merge_node("PMRun", "pm-run", {})
    market = graph.merge_node("MarketData", "market-data:own", props)
    link_run_market(graph, "pm-run", market, run="own")
    return graph


@pytest.mark.parametrize(
    "props",
    [
        {"snapshot": {"benchmark": _BARS}},
        {"window_end": "not-a-date", "snapshot": {"benchmark": _BARS}},
        {"window_end": "2026-08-13", "snapshot": {"benchmark": _BARS}},
        {"window_end": "2026-08-12", "snapshot": "not-a-mapping"},
        {"window_end": "2026-08-12", "snapshot": {"benchmark": []}},
        {"window_end": "2026-08-12", "snapshot": {}},
    ],
    ids=["no-window", "bad-window", "after-as-of", "bad-snapshot", "empty", "absent"],
)
def test_the_runs_own_node_without_a_usable_benchmark_gives_none(
    props: dict[str, object],
) -> None:
    """RPT-OUT-07 / RPT-IDM-03 (DL-246): no usable series on the run's own
    MarketData, or one dated after the as-of, is the no-benchmark path."""
    graph = _linked(props)
    pm_run = graph.get_node("PMRun", "pm-run")
    assert pm_run is not None

    assert run_benchmark(graph, pm_run, as_of=_AS_OF) == ({}, None)


def test_a_broken_lineage_gives_no_benchmark_and_never_another_runs() -> None:
    """RPT-OUT-07 (DL-246): every missing hop is the no-benchmark path."""
    graph = InMemoryGraphStore()
    other = graph.merge_node(
        "MarketData",
        "market-data:other",
        {"window_end": "2026-08-12", "snapshot": {"benchmark": _BARS}},
    )
    link_run_market(graph, "pm-run-other", other, run="other")
    no_source = graph.merge_node("PMRun", "no-source", {})
    bad_source = graph.merge_node("PMRun", "bad-source", {"source_analyst_run_id": 7})
    missing = graph.merge_node("PMRun", "missing", {"source_analyst_run_id": "gone"})
    graph.merge_node("AnalystRun", "orphan", {})
    orphan = graph.merge_node("PMRun", "orphan", {"source_analyst_run_id": "orphan"})
    scan = graph.merge_node("ScanRun", "scan-without-market", {})
    unscanned = graph.merge_node("AnalystRun", "unscanned", {})
    graph.add_edge(scan, unscanned, "ANALYZED_BY")
    no_market = graph.merge_node(
        "PMRun", "no-market", {"source_analyst_run_id": "unscanned"}
    )

    for pm_run in (no_source, bad_source, missing, orphan, no_market):
        assert run_benchmark(graph, pm_run, as_of=_AS_OF) == ({}, None), pm_run.key
