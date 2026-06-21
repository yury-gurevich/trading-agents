"""Analyst graph-poll find_pending + analyze_scan_node tests.

Agent: analyst
Role: verify the analyst finds unprocessed ScanRun nodes and scores them from the
      graph (CandidateSet + MarketData via DERIVED_FROM + same-day RegimeContext),
      marking each processed so it is not re-analyzed.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from agents.analyst.poll import analyze_scan_node, find_pending
from agents.analyst.tests.helpers import bars, candidate, candidate_set
from contracts.common import Provenance
from contracts.provider import (
    MARKET_DATA_LABEL,
    REGIME_CONTEXT_LABEL,
    DataQualityTrace,
    MarketData,
    RegimeContext,
)
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from kernel import GraphStore, Node

_WINDOW_END = "2026-06-22"


def _market_data() -> MarketData:
    return MarketData(
        bars=bars(),
        quality=DataQualityTrace(requested=3, returned=3),
        provenance=Provenance(run_id="provider-md", source_agent="provider"),
    )


def _regime() -> RegimeContext:
    return RegimeContext(
        label="neutral",
        as_of=datetime.now(tz=UTC),
        base_min_confidence=0.55,
        base_stop_loss_pct=0.05,
        base_take_profit_pct=0.10,
        base_max_holding_days=10,
        provenance=Provenance(run_id="provider-rg", source_agent="provider"),
    )


def _seed_scan_run(
    graph: GraphStore,
    *,
    market: bool = True,
    regime: bool = True,
    candidates: bool = True,
) -> Node:
    cset = (
        candidate_set(candidate("AAPL"), candidate("MSFT"))
        if candidates
        else candidate_set()
    )
    scan_run = graph.merge_node(
        "ScanRun", "scan-1", {"candidate_set": cset.model_dump(mode="json")}
    )
    if market:
        market_node = graph.merge_node(
            MARKET_DATA_LABEL,
            f"market-data:{_WINDOW_END}",
            {
                "snapshot": _market_data().model_dump(mode="json"),
                "window_end": _WINDOW_END,
            },
        )
        graph.add_edge(scan_run, market_node, "DERIVED_FROM")
    if regime:
        graph.merge_node(
            REGIME_CONTEXT_LABEL,
            f"regime-context:{_WINDOW_END}",
            {"snapshot": _regime().model_dump(mode="json"), "window_end": _WINDOW_END},
        )
    return scan_run


def test_find_pending_returns_unanalyzed_scan_run() -> None:
    graph = InMemoryGraphStore()
    _seed_scan_run(graph)
    assert len(find_pending(graph)) == 1


def test_find_pending_empty_when_no_scan_run() -> None:
    graph = InMemoryGraphStore()
    assert find_pending(graph) == []


def test_analyze_scan_node_scores_candidates_from_graph() -> None:
    graph = InMemoryGraphStore()
    node = _seed_scan_run(graph)
    analyze_scan_node(node, graph=graph)
    assert len(graph.list_nodes("AnalystRun")) == 1
    # Real scoring ran (market found via DERIVED_FROM), not the empty-market
    # fallback — the happy-path AAPL fixture clears the neutral confidence floor.
    assert len(graph.list_nodes("Recommendation")) >= 1


def test_analyze_scan_node_marks_node_processed() -> None:
    graph = InMemoryGraphStore()
    node = _seed_scan_run(graph)
    analyze_scan_node(node, graph=graph)
    assert find_pending(graph) == []


def test_analyze_scan_node_empty_candidates_still_writes_run() -> None:
    graph = InMemoryGraphStore()
    node = _seed_scan_run(graph, candidates=False)
    analyze_scan_node(node, graph=graph)
    assert len(graph.list_nodes("AnalystRun")) == 1
    assert find_pending(graph) == []


def test_analyze_scan_node_empty_when_market_absent() -> None:
    graph = InMemoryGraphStore()
    node = _seed_scan_run(graph, market=False)
    analyze_scan_node(node, graph=graph)
    assert len(graph.list_nodes("AnalystRun")) == 1


def test_analyze_scan_node_empty_when_regime_absent() -> None:
    graph = InMemoryGraphStore()
    node = _seed_scan_run(graph, regime=False)
    analyze_scan_node(node, graph=graph)
    assert len(graph.list_nodes("AnalystRun")) == 1
