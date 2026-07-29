"""Analyst position-sync branch coverage tests.

Agent: analyst
Role: pin sync-precondition edge cases before graph-pull analysis.
External I/O: none.
"""

from __future__ import annotations

from agents.analyst.poll import find_pending
from contracts.position_sync import (
    POSITION_SYNC_EDGE,
    POSITION_SYNC_PHASE,
    RUN_REQUEST_LABEL,
    position_book_sync_attempted,
    position_book_sync_state,
    run_request_key,
)
from kernel import InMemoryGraphStore


def test_find_pending_waits_when_scan_lacks_market_lineage() -> None:
    """ANLZ-TRG-03 / MON-TRG-04: no MarketData lineage means no analysis."""
    graph = InMemoryGraphStore()
    graph.merge_node("ScanRun", "scan-orphan", {"candidate_set": {"candidates": []}})

    assert find_pending(graph) == []


def test_invalid_sync_marker_status_is_not_attempted() -> None:
    """ANLZ-TRG-03 / MON-TRG-04: planted invalid marker status is ignored."""
    graph = InMemoryGraphStore()
    request = graph.merge_node(
        RUN_REQUEST_LABEL,
        run_request_key("bad-status"),
        {"run_id": "bad-status"},
    )
    marker = graph.merge_node(
        "MonitorRun",
        "position-sync:bad-status",
        {"phase": POSITION_SYNC_PHASE, "position_book_status": "unknown"},
    )
    graph.add_edge(request, marker, POSITION_SYNC_EDGE)

    assert position_book_sync_state(graph, "bad-status") is None
    assert position_book_sync_attempted(graph, "bad-status") is False
