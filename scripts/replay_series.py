"""Series and ledger helpers for S235 replay runner.

Agent: tooling
Role: derive replay windows, convert bars, and settle script-local positions.
External I/O: none.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

from contracts.positions import OpenPosition, PositionStopThreshold
from contracts.provider import OHLCVBar

if TYPE_CHECKING:
    from scripts.replay_broker import ReplayPosition
    from scripts.replay_universe_cache import Universe
    from scripts.sp500_bars import BarRow


def bounded_sessions(
    sessions: tuple[date, ...], start: date | None, end: date | None
) -> tuple[date, ...]:
    return tuple(
        day
        for day in sessions
        if (start is None or day >= start) and (end is None or day <= end)
    )


def bars_by_line(bars: tuple[BarRow, ...]) -> dict[str, tuple[BarRow, ...]]:
    out: dict[str, list[BarRow]] = {}
    for row in bars:
        out.setdefault(row.line, []).append(row)
    return {
        line: tuple(sorted(rows, key=lambda item: item.date))
        for line, rows in out.items()
    }


def members_on(universe: Universe, session: date) -> tuple[str, ...]:
    return tuple(
        sorted(
            episode.line
            for episode in universe.episodes
            if episode.first <= session <= episode.last
        )
    )


def window_bars(
    by_line: dict[str, tuple[BarRow, ...]],
    members: tuple[str, ...],
    session: date,
    days: int,
) -> tuple[BarRow, ...]:
    start = session - timedelta(days=days)
    return tuple(
        row
        for line in members
        for row in by_line.get(line, ())
        if start <= row.date <= session
    )


def contract_bars(rows: tuple[BarRow, ...]) -> tuple[OHLCVBar, ...]:
    return tuple(
        OHLCVBar(
            ticker=row.line,
            bar_date=row.date,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            volume=row.volume,
        )
        for row in rows
    )


def benchmark_window(
    benchmark: dict[date, OHLCVBar], session: date, rows: tuple[BarRow, ...]
) -> tuple[OHLCVBar, ...]:
    dates = {row.date for row in rows} | {session}
    return tuple(benchmark[day] for day in sorted(dates) if day in benchmark)


def held(positions: dict[str, ReplayPosition]) -> tuple[OpenPosition, ...]:
    return tuple(
        OpenPosition(key, pos.quantity, pos.position_ref)
        for key, pos in sorted(positions.items())
    )


def held_stops(
    positions: dict[str, ReplayPosition],
) -> tuple[PositionStopThreshold, ...]:
    return tuple(
        PositionStopThreshold(
            pos.line,
            pos.quantity,
            pos.position_ref,
            pos.entry_price_cents,
            pos.stop_price_cents / pos.entry_price_cents,
        )
        for pos in sorted(positions.values(), key=lambda item: item.line)
    )
