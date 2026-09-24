"""Reporter performance graph-input edge tests.

Agent: reporter
Role: prove malformed optional performance facts are skipped safely.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

import pytest

from agents.reporter.performance_inputs import read_performance_inputs
from kernel import InMemoryGraphStore


def test_performance_inputs_ignore_malformed_optional_facts() -> None:
    """RPT-IDM-03: malformed optional performance facts are ignored, not corrected."""
    graph = InMemoryGraphStore()
    pm_run = graph.merge_node("PMRun", "pm-run", {"created_at": "2026-08-12T22:30:00Z"})
    graph.merge_node(
        "BrokerPositionSnapshot",
        "bad-created-type",
        {
            "status": "fresh",
            "account_status": "fresh",
            "created_at": 12,
            "account_equity_cents": 9,
        },
    )
    graph.merge_node(
        "BrokerPositionSnapshot",
        "bad-created-text",
        {
            "status": "fresh",
            "account_status": "fresh",
            "created_at": "not-a-date",
            "account_equity_cents": 9,
        },
    )
    graph.merge_node(
        "BrokerPositionSnapshot",
        "bad-equity",
        {
            "status": "fresh",
            "account_status": "fresh",
            "created_at": "2026-08-10T22:30:00Z",
            "account_equity_cents": "1000000",
        },
    )
    graph.merge_node(
        "BrokerPositionSnapshot",
        "good",
        {
            "status": "fresh",
            "account_status": "fresh",
            "created_at": "2026-08-11T22:30:00Z",
            "account_equity_cents": 1_000_000,
            "holdings": None,
        },
    )
    graph.merge_node("MarketData", "missing-window", {"snapshot": {"benchmark": []}})
    graph.merge_node(
        "MarketData",
        "bad-window",
        {"window_end": "not-a-date", "snapshot": {"benchmark": []}},
    )
    graph.merge_node(
        "MarketData",
        "empty-benchmark-window",
        {"window_end": "2026-08-11", "snapshot": {"benchmark": []}},
    )
    graph.merge_node(
        "MarketData",
        "good-window",
        {
            "window_end": "2026-08-12",
            "snapshot": {
                "benchmark": [
                    "not-a-bar",
                    {"ticker": "SPY", "bar_date": "not-a-date", "close": 100.0},
                    {"ticker": "SPY", "bar_date": "2026-08-13", "close": 100.0},
                    {"ticker": "SPY", "bar_date": "2026-08-12", "close": "100.0"},
                    {"ticker": "SPY", "bar_date": "2026-08-12", "close": 101.0},
                ]
            },
        },
    )

    inputs = read_performance_inputs(graph, pm_run, inception=date(2026, 8, 10))

    assert inputs.points == ((date(2026, 8, 11), 1_000_000, 0),)
    assert inputs.benchmark_closes == {date(2026, 8, 12): 101.0}
    assert inputs.benchmark_ticker == "SPY"


def test_performance_inputs_reject_invalid_pmrun_created_at() -> None:
    """RPT-IDM-03: PMRun.created_at must define the projection as-of date."""
    graph = InMemoryGraphStore()
    pm_run = graph.merge_node("PMRun", "pm-run", {"created_at": "not-a-date"})

    with pytest.raises(ValueError, match=r"PMRun\.created_at"):
        read_performance_inputs(graph, pm_run, inception=date(2026, 8, 10))
