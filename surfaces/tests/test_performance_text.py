"""Scoreboard wording tests.

Agent: surfaces
Role: pin every sentence shape the vital detail and the chat answer can take.
External I/O: none.
"""

from __future__ import annotations

from surfaces.queries.performance import PerformanceView
from surfaces.queries.performance_text import detail_rows, display, summary
from surfaces.tests.performance_fixtures import MEASURED


def _view(**overrides: float) -> PerformanceView:
    metrics = {**MEASURED, **overrides}
    return PerformanceView("run", "measured", "", "SPY", metrics)


def test_level_lead_and_ahead_recent_read_in_plain_words() -> None:
    """SRF-OUT-07: a displayed 0.00 is level, and a positive recent excess is ahead."""
    text = summary(_view(excess_return_pct=-0.004, rolling_excess_return_pct=0.31))

    assert text.startswith("Level with the market over 32 sessions:")
    assert text.endswith("Over the most recent sessions: ahead by 0.31 pts.")


def test_no_sessions_answer_names_the_run_and_the_reason() -> None:
    """RPT-FAIL-04 / SRF-OUT-07: zero sessions is said, not shown as zeros."""
    view = PerformanceView("empty", "no_sessions", "the reporter found no sessions")

    assert summary(view) == (
        "The scoreboard for run empty has no sessions yet: "
        "the reporter found no sessions."
    )


def test_detail_counts_sessions_without_a_price() -> None:
    """SRF-OUT-07: gap sessions are named beside the session count."""
    rows = dict(detail_rows(_view(performance_gap_sessions=2.0)))

    assert rows["Sessions counted"] == "32 (2 without a price)"
    assert rows["Equity"] == "$102,000.72"
    assert rows["Average invested"] == "21 %"


def test_display_turns_negative_zero_into_zero() -> None:
    """SRF-OUT-07: the reporter's -0.00 -> 0.00 rule, on the rounded value."""
    assert (display(-0.004), display(-0.005), display(0.126)) == (0.0, -0.01, 0.13)
