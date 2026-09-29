"""Settling bar paths for the S241 barrier settlement tests.

Agent: forecaster
Role: build a ticker's daily bars around a claim's ``as_of`` (session 0), weekdays
      only, with the stop and target events a test names, as the settlement reads
      them and as the provider's contract carries them.
External I/O: none.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

from agents.forecaster.domain.barrier_settlement import SettlingBar
from contracts.provider import OHLCVBar

if TYPE_CHECKING:
    from collections.abc import Sequence

#: A Monday: the claim's last bar unless a test says otherwise.
AS_OF = date(2026, 9, 28)
ENTRY = 100.0
STOP, TARGET = 0.05, 0.07


def session_dates(as_of: date, *, before: int, after: int) -> list[date]:
    """Weekdays: ``before`` sessions, then ``as_of``, then ``after`` sessions."""
    back: list[date] = []
    day = as_of
    while len(back) < before:
        day -= timedelta(days=1)
        if day.weekday() < 5:
            back.append(day)
    forward: list[date] = []
    day = as_of
    while len(forward) < after:
        day += timedelta(days=1)
        if day.weekday() < 5:
            forward.append(day)
    return [*reversed(back), as_of, *forward]


def path(
    *,
    events: dict[int, tuple[float, float]] | None = None,
    closes: dict[int, float] | None = None,
    entry: float = ENTRY,
    as_of: date = AS_OF,
    before: int = 2,
    after: int = 10,
) -> list[SettlingBar]:
    """Bars around ``as_of``: session 0 is the as_of bar, 1..after follow it.

    A session closes at its ``closes`` value, else at the prior session's close
    (``entry`` from session 0), with a high 1 % above and a low 1 % below the close,
    unless ``events`` gives that session's ``(high, low)``.
    """
    events = events or {}
    closes = closes or {}
    bars: list[SettlingBar] = []
    close = entry
    days = session_dates(as_of, before=before, after=after)
    for index, day in enumerate(days):
        session = index - before
        close = closes.get(session, entry if session <= 0 else close)
        high, low = events.get(session, (close * 1.01, close * 0.99))
        bars.append(SettlingBar(day, high, low, close))
    return bars


def ohlcv(ticker: str, bars: Sequence[SettlingBar]) -> tuple[OHLCVBar, ...]:
    """The same bars as the provider's contract carries them (open = close)."""
    return tuple(
        OHLCVBar(
            ticker=ticker,
            bar_date=bar.day,
            open=bar.close,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            volume=1_000_000,
        )
        for bar in bars
    )
