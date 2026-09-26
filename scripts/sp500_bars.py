"""Fetch and trim replay bars for S&P 500 membership episodes.

Agent: tooling
Role: map membership episodes to Alpaca source-symbol windows and verify batches.
External I/O: Alpaca market data through an injected or real daily_bars callable.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
from itertools import groupby
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from scripts.sp500_membership import Episode, SymbolMapRow

DEFAULT_BATCH_SIZE = 50  # Alpaca URL size/speed compromise used by the E17.1 spike.


@dataclass(frozen=True)
class BarWindow:
    line: str
    symbol: str
    first: date
    last: date


@dataclass(frozen=True)
class BarRow:
    line: str
    symbol: str
    date: date
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class BarFetchResult:
    rows: tuple[BarRow, ...]
    refetched: tuple[BarWindow, ...]


DailyBars = Callable[..., dict[str, list[Any]]]


def windows_from_episodes(
    episodes: list[Episode] | tuple[Episode, ...],
    symbol_map: list[SymbolMapRow] | tuple[SymbolMapRow, ...],
) -> tuple[BarWindow, ...]:
    rows = tuple(row for row in symbol_map if row.kind == "bars")
    windows: list[BarWindow] = []
    for episode in episodes:
        cursor = episode.first
        overrides = sorted(
            (
                (max(episode.first, row.from_date), min(episode.last, row.to_date), row)
                for row in rows
                if row.line == episode.line
                and row.to_date is not None
                and row.from_date <= episode.last
                and row.to_date >= episode.first
            ),
            key=lambda item: item[0],
        )
        for start, end, row in overrides:
            if cursor < start:
                windows.append(
                    BarWindow(
                        episode.line, episode.ticker, cursor, start - timedelta(days=1)
                    )
                )
            windows.append(BarWindow(episode.line, row.symbol, start, end))
            cursor = end + timedelta(days=1)
        if cursor <= episode.last:
            windows.append(
                BarWindow(episode.line, episode.ticker, cursor, episode.last)
            )
    return tuple(window for window in windows if window.first <= window.last)


def fetch_bars_for_windows(
    windows: list[BarWindow] | tuple[BarWindow, ...],
    sessions: list[date] | tuple[date, ...],
    daily_bars: DailyBars,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> BarFetchResult:
    ordered = sorted(windows, key=lambda item: (item.first, item.last, item.symbol))
    rows: list[BarRow] = []
    refetched: list[BarWindow] = []
    for (_first, _last), group_iter in groupby(
        ordered, key=lambda item: (item.first, item.last)
    ):
        group = tuple(group_iter)
        for chunk in _chunks(group, batch_size):
            symbols = sorted({window.symbol for window in chunk})
            end = _first_end(chunk)
            batch = daily_bars(symbols, end=end, start=_first_start(chunk), asof=end)
            for window in chunk:
                window_rows = _rows_for(batch, window)
                if _is_short(window_rows, window, sessions):
                    refetched.append(window)
                    asof = window.last.isoformat()
                    single = daily_bars(
                        [window.symbol],
                        end=asof,
                        start=window.first.isoformat(),
                        asof=asof,
                    )
                    window_rows = _rows_for(single, window)
                rows.extend(window_rows)
    return BarFetchResult(
        tuple(sorted(rows, key=lambda row: (row.line, row.date))), tuple(refetched)
    )


def _rows_for(payload: dict[str, list[Any]], window: BarWindow) -> tuple[BarRow, ...]:
    rows: list[BarRow] = []
    for raw in payload.get(window.symbol, ()):
        day, open_, high, low, close = raw
        parsed_day = date.fromisoformat(str(day)[:10])
        if window.first <= parsed_day <= window.last:
            rows.append(
                BarRow(
                    window.line,
                    window.symbol,
                    parsed_day,
                    float(open_),
                    float(high),
                    float(low),
                    float(close),
                )
            )
    return tuple(rows)


def _is_short(
    rows: tuple[BarRow, ...], window: BarWindow, sessions: list[date] | tuple[date, ...]
) -> bool:
    expected = {
        session for session in sessions if window.first <= session <= window.last
    }
    if not expected:
        return False
    return not expected.issubset({row.date for row in rows})


def _chunks(
    rows: tuple[BarWindow, ...], size: int
) -> tuple[tuple[BarWindow, ...], ...]:
    return tuple(
        tuple(rows[index : index + size]) for index in range(0, len(rows), size)
    )


def _first_start(windows: tuple[BarWindow, ...]) -> str:
    return min(window.first for window in windows).isoformat()


def _first_end(windows: tuple[BarWindow, ...]) -> str:
    return max(window.last for window in windows).isoformat()
