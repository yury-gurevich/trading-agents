"""Tests for S231 membership-window bar fetching.

Agent: tooling
Role: verify source-symbol windows, batch verification, and ticker-reuse trimming.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

from scripts.sp500_bars import BarWindow, fetch_bars_for_windows, windows_from_episodes
from scripts.sp500_coverage import coverage_report
from scripts.sp500_membership import Episode, SymbolMapRow


def test_ticker_reuse_keeps_bars_inside_each_episode() -> None:
    """S231-A6: reused ticker bars outside the membership windows are discarded."""
    sessions = [date(2020, 1, day) for day in (1, 2, 5, 6)]
    episodes = (
        Episode("DUP", "DUP", date(2020, 1, 1), date(2020, 1, 2)),
        Episode("DUP", "DUP", date(2020, 1, 5), date(2020, 1, 6)),
    )

    def fake_bars(
        symbols: list[str], *, end: str, start: str
    ) -> dict[str, list[tuple[str, float, float, float, float]]]:
        del end, start
        return {
            symbol: [_bar(date(2020, 1, day)) for day in range(1, 7)]
            for symbol in symbols
        }

    windows = windows_from_episodes(episodes, ())
    result = fetch_bars_for_windows(windows, sessions, fake_bars)

    assert len(windows) == 2
    assert [row.date for row in result.rows] == sessions


def test_bars_row_switches_source_inside_range_only() -> None:
    """S231-A7: bars map rows override the source symbol only inside their range."""
    sessions = [date(2020, 1, day) for day in range(1, 5)]
    episodes = (Episode("NEWCO", "NEWCO", date(2020, 1, 1), date(2020, 1, 4)),)
    bars_row = SymbolMapRow(
        "bars", "NEWCO", "OLDCO", date(2020, 1, 1), date(2020, 1, 2), "fixture"
    )

    def fake_bars(
        symbols: list[str], *, end: str, start: str
    ) -> dict[str, list[tuple[str, float, float, float, float]]]:
        start_day, end_day = date.fromisoformat(start), date.fromisoformat(end)
        days = [day for day in sessions if start_day <= day <= end_day]
        return {symbol: [_bar(day) for day in days] for symbol in symbols}

    result = fetch_bars_for_windows(
        windows_from_episodes(episodes, (bars_row,)), sessions, fake_bars
    )

    assert [(row.date, row.symbol) for row in result.rows] == [
        (date(2020, 1, 1), "OLDCO"),
        (date(2020, 1, 2), "OLDCO"),
        (date(2020, 1, 3), "NEWCO"),
        (date(2020, 1, 4), "NEWCO"),
    ]


def test_batch_drop_is_refetched_before_missing() -> None:
    """S231-A8: a batch-omitted symbol is re-fetched singly before it is missing."""
    sessions = [date(2020, 1, 1), date(2020, 1, 2)]
    windows = (
        BarWindow("KEEP", "KEEP", sessions[0], sessions[-1]),
        BarWindow("DROP", "DROP", sessions[0], sessions[-1]),
        BarWindow("EMPTY", "EMPTY", sessions[0], sessions[-1]),
    )
    calls: list[tuple[str, ...]] = []

    def fake_bars(
        symbols: list[str], *, end: str, start: str
    ) -> dict[str, list[tuple[str, float, float, float, float]]]:
        del end, start
        calls.append(tuple(symbols))
        if len(symbols) > 1:
            return {"KEEP": [_bar(day) for day in sessions], "EMPTY": []}
        if symbols == ["DROP"]:
            return {"DROP": [_bar(day) for day in sessions]}
        return {symbols[0]: []}

    result = fetch_bars_for_windows(windows, sessions, fake_bars)
    report = coverage_report(
        tuple(
            Episode(window.line, window.line, window.first, window.last)
            for window in windows
        ),
        result.rows,
        sessions,
    )

    assert ("DROP",) in calls
    assert [row.line for row in result.rows].count("DROP") == 2
    assert {row.reason for row in report.shortfalls} == {"no bars"}
    assert report.shortfalls[0].line == "EMPTY"


def _bar(day: date) -> tuple[str, float, float, float, float]:
    return (day.isoformat(), 1.0, 1.0, 1.0, 1.0)
