"""Tests for S231 coverage accounting over sessions.

Agent: tooling
Role: verify member-session coverage ratios, shortfall reasons, and floor failure.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

import pytest
from scripts.sp500_bars import BarRow
from scripts.sp500_coverage import CoverageReport, coverage_report, require_floor
from scripts.sp500_membership import Episode


def test_coverage_counts_sessions_and_classifies_shortfalls() -> None:
    """S231-A9: coverage uses sessions and reports no bars, late, early, and gap."""
    sessions = [date(2020, 1, day) for day in (1, 2, 3, 6)]
    episodes = tuple(
        Episode(line, line, sessions[0], sessions[-1])
        for line in ("FULL", "LATE", "EARLY", "GAP", "NONE")
    )
    bars = (
        *[_row("FULL", day) for day in sessions],
        *[_row("LATE", day) for day in sessions[1:]],
        *[_row("EARLY", day) for day in sessions[:-1]],
        _row("GAP", sessions[0]),
        _row("GAP", sessions[2]),
        _row("GAP", sessions[3]),
    )

    report = coverage_report(episodes, bars, sessions)

    assert report.member_sessions == 20
    assert report.covered_sessions == 13
    assert report.ratio == 0.65
    assert {row.reason for row in report.shortfalls} == {
        "starts late",
        "ends early",
        "gap",
        "no bars",
    }


def test_coverage_floor_fails_build_below_floor() -> None:
    """S231-A10: the named 0.90 floor exits non-zero when coverage is too low."""
    with pytest.raises(SystemExit):
        require_floor(CoverageReport(100, 89, 0.89, ()))

    require_floor(CoverageReport(100, 90, 0.90, ()))


def _row(line: str, day: date) -> BarRow:
    return BarRow(line, line, day, 1.0, 1.0, 1.0, 1.0)
