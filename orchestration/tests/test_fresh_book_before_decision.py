"""Fresh position-book sync before analyst decision tests.

Agent: orchestration
Role: prove the monitor-sync marker gates analyst graph-pull decisions.
External I/O: none.
"""

from __future__ import annotations

from agents.analyst.poll import analyze_scan_node, find_pending
from agents.analyst.tests.helpers import candidate, candidate_set
from agents.monitor.position_sync import sync_positions_snapshot
from contracts.position_sync import POSITION_BOOK_STALE_INCIDENT
from contracts.positions import open_positions
from kernel import InMemoryGraphStore
from orchestration.tests.fresh_book_helpers import (
    analyst_run,
    holding,
    position,
    recommendation_set,
    scan,
    snapshot,
)


def test_analyst_pending_waits_until_book_synced() -> None:
    """ANLZ-TRG-03 / MON-TRG-04: planted missing sync blocks analyst pending."""
    graph = InMemoryGraphStore()
    scan_node = scan(graph, "c1", candidate_set(candidate("AAPL")))

    assert find_pending(graph) == []
    sync_positions_snapshot(snapshot(graph, "c1", status="stale"), graph=graph)
    assert find_pending(graph) == [scan_node]


def test_2026_07_27_mrvl_sold_book_never_reaches_analyst() -> None:
    """ANLZ-TRG-03 / MON-STA-02: 2026-07-27 MRVL sell regression is impossible."""
    graph = InMemoryGraphStore()
    position(graph, "pm-run:MRVL", "MRVL", 44, 8500)
    scan_node = scan(graph, "c2", candidate_set())

    assert [
        (position.ticker, position.quantity) for position in open_positions(graph)
    ] == [("MRVL", 44)]
    sync_positions_snapshot(snapshot(graph, "c2"), graph=graph)
    assert open_positions(graph) == ()

    analyze_scan_node(scan_node, graph=graph)

    rec_set = recommendation_set(graph)
    seen = {
        item["ticker"]
        for item in (
            *rec_set["recommendations"],
            *rec_set["rejections"],
        )
    }
    assert "MRVL" not in seen
    assert analyst_run(graph).props["held_count"] == 0
    assert all(
        node.props["ticker"] != "MRVL" for node in graph.list_nodes("Recommendation")
    )


def test_stale_book_degrades_but_still_writes_recommendation_set() -> None:
    """ANLZ-FAIL-01 / MON-FAIL-01: stale sync is fail-visible, not fail-closed."""
    graph = InMemoryGraphStore()
    scan_node = scan(graph, "c3", candidate_set(candidate("AAPL")))
    sync_positions_snapshot(
        snapshot(graph, "c3", status="stale", reason="broker unavailable"),
        graph=graph,
    )

    analyze_scan_node(scan_node, graph=graph)

    rec_set = recommendation_set(graph)
    assert rec_set["provenance"]["incident_refs"] == (POSITION_BOOK_STALE_INCIDENT,)
    assert graph.list_nodes("AnalystRun")
    assert "position book stale" in graph.list_nodes("Fault")[0].props["message"]


def test_synced_held_tickers_still_reach_scoring_universe() -> None:
    """ANLZ-IN-03 / MON-IDN-02: empty candidates still score synced held tickers."""
    graph = InMemoryGraphStore()
    scan_node = scan(graph, "c4", candidate_set())
    sync_positions_snapshot(
        snapshot(
            graph,
            "c4",
            holdings=(
                holding("AAPL", 3, 10000),
                holding("MSFT", 5, 20000),
            ),
        ),
        graph=graph,
    )

    analyze_scan_node(scan_node, graph=graph)

    rec_set = recommendation_set(graph)
    seen = {
        item["ticker"]
        for item in (
            *rec_set["recommendations"],
            *rec_set["rejections"],
        )
    }
    assert seen == {"AAPL", "MSFT"}
    assert analyst_run(graph).props["held_count"] == 2
