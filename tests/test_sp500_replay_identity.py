"""Tests for S233 replay identity pinning and switch chaining.

Agent: tooling
Role: verify synthetic issuer identity and source-switch price continuity.
External I/O: none.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest
from scripts.sp500_bars import BarRow, BarWindow, fetch_bars_for_windows
from scripts.sp500_chain import chain_source_switches

BarsPayload = dict[str, list[tuple[Any, ...]]]


def test_every_bar_window_fetch_is_pinned_to_window_last_day() -> None:
    """S233-A1: every replay bar request is pinned `asof` its window's last day."""
    sessions = [date(2020, 1, day) for day in (2, 3, 6, 7)]
    windows = (
        BarWindow("AAA", "AAA", date(2020, 1, 2), date(2020, 1, 3)),
        BarWindow("BBB", "BBB", date(2020, 1, 2), date(2020, 1, 3)),
        BarWindow("OK", "OK", date(2020, 1, 6), date(2020, 1, 7)),
        BarWindow("SHORT", "SHORT", date(2020, 1, 6), date(2020, 1, 7)),
    )
    calls: list[dict[str, Any]] = []

    def fake_bars(symbols: list[str], **kwargs: Any) -> BarsPayload:
        calls.append({"symbols": tuple(symbols), **kwargs})
        if symbols == ["SHORT"] and kwargs.get("asof") == "2020-01-07":
            return {"SHORT": [_bar(day, 30.0) for day in sessions[2:]]}
        if "SHORT" in symbols:
            return {
                "OK": [_bar(day, 40.0) for day in sessions[2:]],
                "SHORT": [_bar(sessions[2], 30.0)],
            }
        return {symbol: [_bar(day, 10.0) for day in sessions[:2]] for symbol in symbols}

    result = fetch_bars_for_windows(windows, sessions, fake_bars, batch_size=10)

    assert [call["asof"] for call in calls] == [
        "2020-01-03",
        "2020-01-07",
        "2020-01-07",
    ]
    assert [row.date for row in result.rows if row.line == "SHORT"] == sessions[2:]


def test_reused_ticker_keeps_issuer_when_asof_is_pinned() -> None:
    """S233-A3: a reused ticker keeps its issuer when fetched as of the window end."""
    sessions = [date(2018, 11, 7), date(2018, 11, 8)]
    window = BarWindow("XYZ", "XYZ", sessions[0], sessions[-1])

    def fake_bars(symbols: list[str], **kwargs: Any) -> BarsPayload:
        assert symbols == ["XYZ"]
        issuer_a = kwargs.get("asof") == "2018-11-08"
        close = 18.0 if issuer_a else 57.62
        return {"XYZ": [_bar(day, close) for day in sessions]}

    result = fetch_bars_for_windows((window,), sessions, fake_bars)

    assert [row.close for row in result.rows] == [18.0, 18.0]


def test_switch_is_chained_on_raw_boundary_closes() -> None:
    """S233-A4: a source switch is chained on raw closes, not adjusted levels."""
    first = date(2020, 11, 16)
    second = date(2020, 11, 17)
    rows = (
        BarRow("VTRS", "MYL", first, 100.0, 110.0, 90.0, 100.0),
        BarRow("VTRS", "VTRS", second, 80.0, 88.0, 72.0, 80.0),
    )

    def raw_close(symbol: str, day: date, asof: date) -> float:
        assert (symbol, day, asof) in {
            ("MYL", first, first),
            ("VTRS", second, second),
        }
        return {("MYL", first): 15.855, ("VTRS", second): 16.34}[(symbol, day)]

    result = chain_source_switches(
        rows, raw_close, spy_closes={first: 100.0, second: 101.0}
    )

    chained = result.rows
    assert chained[-1].close == 80.0
    assert chained[-1].close / chained[-2].close == pytest.approx(16.34 / 15.855)
    assert chained[-2].high / chained[-2].close == pytest.approx(110.0 / 100.0)
    assert result.switches[0].raw_move == pytest.approx(16.34 / 15.855 - 1.0)


def test_chaining_runs_backwards_through_multiple_switches() -> None:
    """S233-A5: chain factors compose backwards and record each source switch."""
    days = [date(2020, 1, day) for day in range(1, 7)]
    rows = (
        BarRow("PSKY", "AAA", days[0], 100.0, 100.0, 100.0, 100.0),
        BarRow("PSKY", "AAA", days[1], 110.0, 110.0, 110.0, 110.0),
        BarRow("PSKY", "BBB", days[2], 50.0, 50.0, 50.0, 50.0),
        BarRow("PSKY", "BBB", days[3], 60.0, 60.0, 60.0, 60.0),
        BarRow("PSKY", "CCC", days[4], 200.0, 200.0, 200.0, 200.0),
        BarRow("PSKY", "CCC", days[5], 300.0, 300.0, 300.0, 300.0),
    )
    raw = {
        ("AAA", days[1], days[1]): 10.0,
        ("BBB", days[2], days[3]): 12.0,
        ("BBB", days[3], days[3]): 12.0,
        ("CCC", days[4], days[5]): 18.0,
    }

    def raw_close(symbol: str, day: date, asof: date) -> float:
        return raw[(symbol, day, asof)]

    result = chain_source_switches(
        rows, raw_close, spy_closes=dict.fromkeys(days, 100.0)
    )
    by_date = {row.date: row for row in result.rows}

    assert by_date[days[5]].close == 300.0
    assert by_date[days[4]].close / by_date[days[3]].close == pytest.approx(18.0 / 12.0)
    assert by_date[days[2]].close / by_date[days[1]].close == pytest.approx(12.0 / 10.0)
    assert [row.from_symbol + "->" + row.to_symbol for row in result.switches] == [
        "AAA->BBB",
        "BBB->CCC",
    ]
    assert result.switches[1].move_vs_spy == pytest.approx(0.5)


def _bar(day: date, close: float) -> tuple[str, float, float, float, float]:
    return (day.isoformat(), close, close, close, close)
