"""Original seven graph-pull cases, also used by S242's same-work oracles.

Agent: tooling
Role: retain S242's seeds and exact expected keys while splitting the shared spy.
External I/O: none (in-memory graph).
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from tests.poll_payload_support import NOW as NOW
from tests.poll_payload_support import PayloadSpy as PayloadSpy
from tests.poll_payload_support import PollCase as PollCase
from tests.poll_payload_support import seed_chain

from agents.provider.tests.barrier_history_helpers import analyst_run, rec

if TYPE_CHECKING:
    from kernel import GraphStore


def seed_analyst(graph: GraphStore) -> None:
    """ScanRuns: synced (pending), analysed, unsynced, and with no MarketData."""
    seed_chain(graph, "ScanRun", "ANALYZED_BY", "AnalystRun")
    graph.merge_node("ScanRun", "d", {})
    for scan, run_id in (("c", "synced"), ("b", "synced"), ("a", "unsynced")):
        market = graph.merge_node("MarketData", f"md-{scan}", {"run_id": run_id})
        node = graph.get_node("ScanRun", scan)
        assert node is not None
        graph.add_edge(node, market, "DERIVED_FROM")
    request = graph.merge_node("RunRequest", "run-request:synced", {})
    marker = graph.merge_node(
        "MonitorRun",
        "position-sync:synced",
        {"phase": "sync", "position_book_status": "fresh"},
    )
    graph.add_edge(request, marker, "POSITION_SYNCED_BY")


def seed_reporter(graph: GraphStore) -> None:
    """MonitorRuns: a sync marker (never reported), one pending, one reported."""
    graph.merge_node("MonitorRun", "sync", {"phase": "sync"})
    seed_chain(graph, "MonitorRun", "REPORTED_BY", "Snapshot")


def seed_barrier(graph: GraphStore) -> None:
    """71 stale AnalystRuns with a qualifying buy, and one current (A8)."""
    stale = (NOW - timedelta(days=2)).isoformat()
    for index in range(71):
        key = f"stale-{index:02d}"
        analyst_run(graph, rec("AAPL", "buy"), key=key)
        graph.merge_node("AnalystRun", key, {"created_at": stale})
    analyst_run(graph, rec("AAPL", "buy"), key="current")
    current = (NOW - timedelta(hours=1)).isoformat()
    graph.merge_node("AnalystRun", "current", {"created_at": current})


def _simple(name: str, label: str, edge: str) -> PollCase:
    return PollCase(
        name,
        label,
        edge,
        lambda graph: seed_chain(graph, label, edge, "Done"),
        ("c", "a"),
        ("c", "a"),
    )


CASES = (
    _simple("provider", "RunRequest", "INGESTED_BY"),
    _simple("scanner", "MarketData", "SCANNED_BY"),
    PollCase(
        "analyst", "ScanRun", "ANALYZED_BY", seed_analyst, ("c", "a", "d"), ("c",)
    ),
    _simple("portfolio_manager", "AnalystRun", "EVALUATED_BY"),
    _simple("monitor", "ExecutionRun", "MONITORED_BY"),
    PollCase(
        "reporter",
        "MonitorRun",
        "REPORTED_BY",
        seed_reporter,
        ("sync", "c", "a"),
        ("c", "a"),
    ),
    PollCase(
        "barrier_history",
        "AnalystRun",
        "BARRIER_HISTORY_BY",
        seed_barrier,
        ("current",),
        ("current",),
    ),
)
