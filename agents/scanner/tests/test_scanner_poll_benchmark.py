"""Scanner beta-cap-from-the-graph tests (S195).

Agent: scanner
Role: verify the graph-pull scan evaluates the beta cap when the snapshot carries a
      benchmark, and records it skipped — never passed — when it does not.
External I/O: none.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from agents.scanner.poll import scan_market_node
from agents.scanner.settings import ScannerSettings
from contracts.common import Provenance
from contracts.provider import (
    MARKET_DATA_LABEL,
    DataQualityTrace,
    MarketData,
    OHLCVBar,
)
from contracts.scanner import CandidateSet
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from kernel import GraphStore

_START = date(2026, 1, 2)
_WINDOW_END = "2026-01-06"


def _bars(ticker: str, closes: tuple[float, ...]) -> tuple[OHLCVBar, ...]:
    return tuple(
        OHLCVBar(
            ticker=ticker,
            bar_date=date.fromordinal(_START.toordinal() + offset),
            open=close,
            high=close,
            low=close,
            close=close,
            volume=1_000_000,
        )
        for offset, close in enumerate(closes)
    )


# HIGHB tracks the benchmark at roughly 3x; LOWB at roughly 0.6x.
_BENCHMARK = _bars("SPY", (100.0, 101.0, 102.0, 103.0, 104.0))
_CANDIDATES = (
    *_bars("HIGHB", (100.0, 103.0, 106.0, 109.0, 112.0)),
    *_bars("LOWB", (100.0, 100.6, 101.2, 101.8, 102.5)),
)


def _seed(graph: GraphStore, *, benchmark: tuple[OHLCVBar, ...]) -> None:
    market = MarketData(
        bars=_CANDIDATES,
        benchmark=benchmark,
        quality=DataQualityTrace(requested=2, returned=2),
        provenance=Provenance(run_id="provider-1", source_agent="provider"),
    )
    graph.merge_node(
        MARKET_DATA_LABEL,
        "market-data:r1",
        {
            "snapshot": market.model_dump(mode="json"),
            "tickers": ["HIGHB", "LOWB"],
            "window_end": _WINDOW_END,
        },
    )


def _scan(graph: InMemoryGraphStore) -> CandidateSet:
    node = graph.list_nodes(MARKET_DATA_LABEL)[0]
    scan_market_node(node, graph=graph, settings=ScannerSettings())
    scan_run = graph.list_nodes("ScanRun")[0]
    return CandidateSet.model_validate(scan_run.props["candidate_set"])


def test_beta_cap_gates_when_the_snapshot_carries_a_benchmark() -> None:
    """With a benchmark, max_beta is evaluated and drops the high-beta name."""
    graph = InMemoryGraphStore()
    _seed(graph, benchmark=_BENCHMARK)
    candidate_set = _scan(graph)
    survivors = {c.ticker for c in candidate_set.candidates}
    assert survivors == {"LOWB"}
    assert candidate_set.filter_trace.dropped_by_filter["max_beta"] == 1
    for candidate in candidate_set.candidates:
        assert "max_beta" in candidate.survived_filters
        assert "max_beta" not in candidate.skipped_filters


def test_beta_cap_is_skipped_not_passed_without_a_benchmark() -> None:
    """The deployed defect: no benchmark means the cap never gates, and says so."""
    graph = InMemoryGraphStore()
    _seed(graph, benchmark=())
    candidate_set = _scan(graph)
    survivors = {c.ticker for c in candidate_set.candidates}
    assert survivors == {"HIGHB", "LOWB"}
    assert "max_beta" not in candidate_set.filter_trace.dropped_by_filter
    for candidate in candidate_set.candidates:
        assert "max_beta" in candidate.skipped_filters
        assert "max_beta" not in candidate.survived_filters
