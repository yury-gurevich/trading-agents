"""Scanner earnings-window attestation tests (S196).

Agent: scanner
Role: verify a missing earnings date is recorded as a pass when the producer's
      horizon covers the exclusion window, and as skipped when it cannot.
External I/O: none.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from agents.scanner.domain.filter_attestation import evaluate_filters
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

_SETTINGS = ScannerSettings()
_CLEAN = {"latest_close": 50.0, "average_volume": 1_000_000.0, "relative_strength": 0.5}


def test_absence_passes_when_the_horizon_covers_the_exclusion_window() -> None:
    """30 days of coverage answers a 5-day question: no date means no earnings due."""
    fired, passed, skipped = evaluate_filters(dict(_CLEAN), _SETTINGS, 30)
    assert fired is None
    assert "earnings_window" in passed
    assert "earnings_window" not in skipped


def test_absence_is_skipped_when_no_horizon_was_declared() -> None:
    """Without a declared horizon the map may simply be missing data."""
    fired, passed, skipped = evaluate_filters(dict(_CLEAN), _SETTINGS, None)
    assert fired is None
    assert "earnings_window" in skipped
    assert "earnings_window" not in passed


def test_absence_is_skipped_when_the_horizon_only_equals_the_window() -> None:
    """An equal horizon leaves the boundary day unproven, so it is not an answer."""
    _, passed, skipped = evaluate_filters(
        dict(_CLEAN), _SETTINGS, _SETTINGS.earnings_exclusion_days
    )
    assert "earnings_window" in skipped
    assert "earnings_window" not in passed


def test_a_known_date_still_decides_regardless_of_horizon() -> None:
    """The horizon only speaks about absence; a real date is judged as before."""
    inside = {**_CLEAN, "days_to_earnings": 2.0}
    outside = {**_CLEAN, "days_to_earnings": 40.0}
    assert evaluate_filters(inside, _SETTINGS, 30)[0] == "earnings_window"
    assert evaluate_filters(inside, _SETTINGS, None)[0] == "earnings_window"
    assert "earnings_window" in evaluate_filters(outside, _SETTINGS, None)[1]


def _bars(ticker: str) -> tuple[OHLCVBar, ...]:
    return tuple(
        OHLCVBar(
            ticker=ticker,
            bar_date=date(2026, 1, 2 + offset),
            open=100.0 + offset,
            high=100.0 + offset,
            low=100.0 + offset,
            close=100.0 + offset,
            volume=1_000_000,
        )
        for offset in range(4)
    )


def _seed(graph: GraphStore, *, horizon: int | None) -> None:
    market = MarketData(
        bars=_bars("AAPL"),
        earnings={},
        earnings_horizon_days=horizon,
        quality=DataQualityTrace(requested=1, returned=1),
        provenance=Provenance(run_id="provider-1", source_agent="provider"),
    )
    graph.merge_node(
        MARKET_DATA_LABEL,
        "market-data:r1",
        {
            "snapshot": market.model_dump(mode="json"),
            "tickers": ["AAPL"],
            "window_end": "2026-01-05",
        },
    )


def _scan(graph: InMemoryGraphStore) -> CandidateSet:
    node = graph.list_nodes(MARKET_DATA_LABEL)[0]
    scan_market_node(node, graph=graph, settings=ScannerSettings())
    return CandidateSet.model_validate(
        graph.list_nodes("ScanRun")[0].props["candidate_set"]
    )


def test_graph_pull_scan_passes_the_gate_when_the_snapshot_declares_a_horizon() -> None:
    """The deployed path: a declared horizon turns the skip into a certified pass."""
    graph = InMemoryGraphStore()
    _seed(graph, horizon=30)
    candidate = _scan(graph).candidates[0]
    assert "earnings_window" in candidate.survived_filters
    assert "earnings_window" not in candidate.skipped_filters


def test_graph_pull_scan_skips_the_gate_without_a_horizon() -> None:
    """The pre-S196 shape, pinned: no horizon means the gate stays uncertified."""
    graph = InMemoryGraphStore()
    _seed(graph, horizon=None)
    candidate = _scan(graph).candidates[0]
    assert "earnings_window" in candidate.skipped_filters
    assert "earnings_window" not in candidate.survived_filters
