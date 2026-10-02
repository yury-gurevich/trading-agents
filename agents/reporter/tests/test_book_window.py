"""A run's book metrics come from the broker's fills in its window (S253).

Agent: reporter
Role: prove the window, the counts and the outcomes since the inception.
External I/O: none.
"""

from __future__ import annotations

from agents.reporter.result import build_snapshot
from agents.reporter.tests.book_fixtures import (
    PREVIOUS_AT,
    PREVIOUS_RUN,
    REPORTED_RUN,
    SETTINGS,
    filled,
    pm_run,
    seed_sched_2026_10_01,
)
from kernel import InMemoryGraphStore


def test_the_runs_snapshot_counts_the_fills_in_its_window() -> None:
    """RPT-OUT-02 / RPT-IN-01: sched-2026-10-01 opened 1 and closed 3, all stops.

    The run's own four buys are in its lineage, unfilled, and count for nothing.
    """
    graph = InMemoryGraphStore()
    seed_sched_2026_10_01(graph)

    snapshot = build_snapshot(graph, REPORTED_RUN, settings=SETTINGS)

    portfolio = snapshot.portfolio_metrics
    assert portfolio["positions_opened"] == 1.0
    assert portfolio["positions_closed"] == 3.0
    assert portfolio["close_trigger_stop"] == 3.0
    assert snapshot.headline.summary.startswith("1 positions opened; 3 closed; ")


def test_outcomes_are_cumulative_since_the_inception() -> None:
    """RPT-OUT-02 / RPT-NEV-03: four stops since the inception, no wins.

    Profit factor 0.0 is a real value here, not an undefined one. The sell refreshed
    before the inception is not counted. One winning exit makes it wins / losses.
    """
    graph = InMemoryGraphStore()
    seed_sched_2026_10_01(graph)

    portfolio = build_snapshot(graph, REPORTED_RUN, settings=SETTINGS).portfolio_metrics

    assert portfolio["closed_trades_with_pnl"] == 4.0
    assert portfolio["profit_factor"] == 0.0
    assert portfolio["expectancy_cents"] == -3_632.25

    won = InMemoryGraphStore()
    seed_sched_2026_10_01(won)
    filled(
        won,
        "target:MSFT",
        side="sell",
        refreshed_at="2026-10-01T22:30:53+00:00",
        pnl_cents=7_264,
    )
    outcomes = build_snapshot(won, REPORTED_RUN, settings=SETTINGS).portfolio_metrics
    assert outcomes["closed_trades_with_pnl"] == 5.0
    assert outcomes["profit_factor"] == 7_264 / 14_529
    assert outcomes["expectancy_cents"] == (7_264 - 14_529) / 5


def test_a_fill_belongs_to_one_window() -> None:
    """RPT-IDM-04 / RPT-OUT-02: each filled fill is counted once, by one run.

    The older stop is the previous run's, not this one's. A fill refreshed exactly at
    a run's `created_at` belongs to that run, never to the next.
    """
    graph = InMemoryGraphStore()
    seed_sched_2026_10_01(graph)
    pm_run(graph, "sched-2026-09-29", "2026-09-30T03:00:00+00:00")
    filled(graph, "at-boundary:KO", side="buy", refreshed_at=PREVIOUS_AT)

    previous = build_snapshot(graph, PREVIOUS_RUN, settings=SETTINGS)
    reported = build_snapshot(graph, REPORTED_RUN, settings=SETTINGS)

    assert _counts(previous.portfolio_metrics) == (1.0, 1.0, 1.0)
    assert _counts(reported.portfolio_metrics) == (1.0, 3.0, 3.0)


def test_re_reporting_an_old_run_reproduces_its_book_metrics() -> None:
    """RPT-IDM-04 / RPT-IDM-01: a later run and later fills change nothing.

    Nothing refreshed after the run's `created_at` is read, and the window's start is
    another PMRun's `created_at`, never the reporter's own earlier Snapshot.
    """
    then = InMemoryGraphStore()
    seed_sched_2026_10_01(then)
    first = build_snapshot(then, REPORTED_RUN, settings=SETTINGS).portfolio_metrics

    graph = InMemoryGraphStore()
    seed_sched_2026_10_01(graph)
    pm_run(graph, "sched-2026-10-02", "2026-10-02T22:40:00+00:00")
    filled(graph, "later:NVDA", side="buy", refreshed_at="2026-10-02T14:30:00+00:00")
    filled(
        graph,
        "later-stop:TGT",
        side="sell",
        refreshed_at="2026-10-02T15:00:00+00:00",
        pnl_cents=-1_000,
        stop=True,
    )
    again = build_snapshot(graph, REPORTED_RUN, settings=SETTINGS).portfolio_metrics

    assert again == first
    assert _counts(again) == (1.0, 3.0, 3.0)
    assert again["closed_trades_with_pnl"] == 4.0


def test_the_first_run_has_no_window_start() -> None:
    """RPT-OUT-02: with no earlier PMRun, every fill up to the run is its own."""
    graph = InMemoryGraphStore()
    pm_run(graph, "first", "2026-08-12T22:40:00+00:00")
    filled(graph, "early:AAPL", side="buy", refreshed_at="2026-07-01T14:30:00Z")
    filled(graph, "naive:MSFT", side="buy", refreshed_at="2026-08-11T14:30:00")
    filled(graph, "after:AMZN", side="buy", refreshed_at="2026-08-13T14:30:00Z")
    filled(graph, "garbled:IBM", side="buy", refreshed_at="yesterday")

    portfolio = build_snapshot(graph, "first", settings=SETTINGS).portfolio_metrics

    assert _counts(portfolio) == (2.0, 0.0, 0.0)


def test_a_run_without_created_at_has_no_book_counts() -> None:
    """RPT-NEV-03 / RPT-OUT-02: an undefined count is absent, and nothing raises.

    The headline prints `?` where a count it cannot know would stand.
    """
    graph = InMemoryGraphStore()
    seed_sched_2026_10_01(graph)
    pm_run(graph, "undated", None)
    pm_run(graph, "garbled", "not-a-time")

    snapshot = build_snapshot(graph, "undated", settings=SETTINGS)

    for key in (
        "positions_opened",
        "positions_closed",
        "close_trigger_stop",
        "closed_trades_with_pnl",
        "profit_factor",
        "expectancy_cents",
    ):
        assert key not in snapshot.portfolio_metrics
    assert snapshot.portfolio_metrics["approved_count"] == 4.0
    assert snapshot.headline.summary.startswith("? positions opened; ? closed; ")
    assert _counts(
        build_snapshot(graph, REPORTED_RUN, settings=SETTINGS).portfolio_metrics
    ) == (1.0, 3.0, 3.0)


def _counts(portfolio: dict[str, float]) -> tuple[float, float, float]:
    return (
        portfolio["positions_opened"],
        portfolio["positions_closed"],
        portfolio["close_trigger_stop"],
    )
