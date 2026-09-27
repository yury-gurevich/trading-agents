"""The S235 replay cache as S237 Layer 2 reads it: SIP volume and cache bars.

Agent: tooling
Role: map a live ticker to its cache line and swap a snapshot's volume or bars for
      the cache's, over the S235 replay's own window.
External I/O: reads the local replay cache directory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from scripts.replay_cache import load_replay_cache
from scripts.replay_series import (
    bars_by_line,
    benchmark_window,
    contract_bars,
    window_bars,
)

from orchestration.history_window import declared_lookback_days

if TYPE_CHECKING:
    from datetime import date
    from pathlib import Path

    from scripts.replay_settings import ReplaySettings
    from scripts.sp500_bars import BarRow
    from scripts.sp500_membership import Episode

    from contracts.provider import MarketData, OHLCVBar


@dataclass(frozen=True)
class CacheContext:
    """The cache's bars by line, its membership episodes and its SPY."""

    line_bars: dict[str, tuple[BarRow, ...]]
    episodes: tuple[Episode, ...]
    benchmark: dict[date, OHLCVBar]
    _dated: dict[str, dict[date, BarRow]] = field(default_factory=dict)

    def bar(self, line: str, day: date) -> BarRow | None:
        """Return the cache's bar for one line and date, if it holds one."""
        if line not in self._dated:
            self._dated[line] = {row.date: row for row in self.line_bars.get(line, ())}
        return self._dated[line].get(day)


def load_cache(path: Path) -> CacheContext:
    """Load the S235 cache once, refusing one without volume (as S235 does)."""
    context = load_replay_cache(path)
    return CacheContext(
        bars_by_line(context.universe.bars),
        context.universe.episodes,
        context.benchmark,
    )


def lines_for(
    context: CacheContext, tickers: tuple[str, ...], session: date
) -> dict[str, str]:
    """Each live ticker's cache line: the episode naming it on the session date."""
    lines: dict[str, str] = {}
    for ticker in tickers:
        episode = next(
            (
                item
                for item in context.episodes
                if item.ticker == ticker and item.first <= session <= item.last
            ),
            None,
        )
        line = episode.line if episode is not None else ticker
        if line in context.line_bars:
            lines[ticker] = line
    return lines


def sip_volume(
    context: CacheContext, market: MarketData, lines: dict[str, str]
) -> tuple[MarketData, int]:
    """Step 1: each bar's volume from its cache twin; bars without one are counted."""
    bars: list[OHLCVBar] = []
    unswapped = 0
    for bar in market.bars:
        line = lines.get(bar.ticker)
        twin = context.bar(line, bar.bar_date) if line else None
        if twin is None:
            unswapped += 1
            bars.append(bar)
        else:
            bars.append(bar.model_copy(update={"volume": twin.volume}))
    return market.model_copy(update={"bars": tuple(bars)}), unswapped


def cache_bars(
    context: CacheContext,
    market: MarketData,
    lines: dict[str, str],
    session: date,
    settings: ReplaySettings,
) -> MarketData:
    """Step 5: the cache's bars and SPY over the S235 window, under live tickers."""
    days = declared_lookback_days(
        settings.analyst,
        as_of=session,
        staleness_buffer_sessions=settings.provider.max_staleness_days,
    )
    rows = window_bars(context.line_bars, tuple(lines.values()), session, days)
    ticker_of = {line: ticker for ticker, line in lines.items()}
    bars = tuple(
        bar.model_copy(update={"ticker": ticker_of[bar.ticker]})
        for bar in contract_bars(rows)
    )
    return market.model_copy(
        update={
            "bars": bars,
            "benchmark": benchmark_window(context.benchmark, session, rows),
        }
    )
