"""Which broker snapshot stands for a day in the performance series.

Agent: reporter
Role: prove a day's point is the latest fresh snapshot the run could see.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

from agents.reporter.performance_inputs import read_performance_inputs
from kernel import InMemoryGraphStore, Node


def test_the_day_point_is_the_latest_fresh_snapshot_of_the_date() -> None:
    """RPT-OUT-07: a date's point is its last fresh snapshot, nearest the close."""
    graph = InMemoryGraphStore()
    pm_run = _pm_run(graph, "2026-08-11T22:30:00Z")
    # Written late-first: the choice is by timestamp, not by listing order.
    _snapshot(graph, "late", "2026-08-10T22:44:00Z", 2_000_000)
    _snapshot(graph, "early", "2026-08-10T22:30:00Z", 1_000_000)
    _snapshot(graph, "stale", "2026-08-10T22:50:00Z", 3_000_000, status="stale")

    inputs = read_performance_inputs(graph, pm_run, inception=date(2026, 8, 10))

    assert inputs.points == ((date(2026, 8, 10), 2_000_000, 500_000),)


def test_a_two_run_day_uses_the_post_close_sync_not_the_intraday_one() -> None:
    """RPT-OUT-07 / RPT-IDM-03: 2026-09-24: intraday 14:15, post-close 22:30."""
    graph = InMemoryGraphStore()
    pm_run = _pm_run(graph, "2026-09-24T22:41:39.077382+00:00")
    _snapshot(graph, "manual", "2026-09-24T14:15:13.367215+00:00", 10_200_072)
    _snapshot(graph, "manual-pm", "2026-09-24T14:24:26.630397+00:00", 10_199_769)
    _snapshot(graph, "sched", "2026-09-24T22:30:43.055790+00:00", 10_196_728)
    _snapshot(graph, "after-pm", "2026-09-24T22:41:57.144299+00:00", 10_196_502)

    inputs = read_performance_inputs(graph, pm_run, inception=date(2026, 9, 24))

    assert inputs.points == ((date(2026, 9, 24), 10_196_728, 500_000),)


def test_a_snapshot_created_after_the_pm_run_is_never_read() -> None:
    """RPT-IDM-03: a re-report reproduces its figures after later same-day syncs."""
    graph = InMemoryGraphStore()
    pm_run = _pm_run(graph, "2026-08-11T22:40:00Z")
    _snapshot(graph, "prior", "2026-08-10T22:30:00Z", 1_000_000)
    _snapshot(graph, "sync", "2026-08-11T22:30:00Z", 1_010_000)
    before = read_performance_inputs(graph, pm_run, inception=date(2026, 8, 10))

    _snapshot(graph, "later-same-day", "2026-08-11T23:10:00Z", 1_500_000)
    after = read_performance_inputs(graph, pm_run, inception=date(2026, 8, 10))

    assert after.points == before.points
    assert before.points[-1] == (date(2026, 8, 11), 1_010_000, 500_000)


def _pm_run(graph: InMemoryGraphStore, created_at: str) -> Node:
    return graph.merge_node("PMRun", "pm-run", {"created_at": created_at})


def _snapshot(
    graph: InMemoryGraphStore,
    key: str,
    created_at: str,
    equity_cents: int,
    *,
    status: str = "fresh",
) -> None:
    graph.merge_node(
        "BrokerPositionSnapshot",
        key,
        {
            "status": status,
            "account_status": "fresh",
            "created_at": created_at,
            "account_equity_cents": equity_cents,
            "holdings": [{"market_value_cents": 500_000}],
        },
    )
