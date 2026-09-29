"""Extreme-move guard fixtures (S243 / DL-247).

Agent: provider
Role: build a batch of daily bars for many names over many sessions, with ordinary
      moves everywhere except the extreme days a test places on purpose, so a test
      can put a real history day or a bad newest print exactly where it wants.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from contracts.provider import OHLCVBar

TODAY = datetime.now(tz=UTC).date()
#: A session index counted from the end: -1 is each name's newest bar.
NEWEST = -1


def names(count: int, *extra: str) -> tuple[str, ...]:
    """``count`` filler names plus the named ``extra`` ones, in that order."""
    return (*(f"N{index:03d}" for index in range(count)), *extra)


def calm_move(name_index: int, session: int) -> float:
    """An ordinary open-to-close move in [-1 %, +1 %], deterministic."""
    return 0.005 * ((name_index * 7 + session * 13) % 5 - 2)


def batch(
    tickers: tuple[str, ...],
    sessions: int,
    *,
    shocks: dict[tuple[str, int], float] | None = None,
    lag: dict[str, int] | None = None,
) -> tuple[OHLCVBar, ...]:
    """``sessions`` consecutive daily bars per ticker, the last one dated today.

    ``shocks`` sets a ticker's open-to-close move on one session (a negative index
    counts from the end); ``lag`` drops a ticker's last N sessions, so its newest
    bar is older than the batch's.
    """
    moves = {
        (ticker, session % sessions): move
        for (ticker, session), move in (shocks or {}).items()
    }
    rows: list[OHLCVBar] = []
    for name_index, ticker in enumerate(tickers):
        for session in range(sessions - (lag or {}).get(ticker, 0)):
            move = moves.get((ticker, session), calm_move(name_index, session))
            rows.append(_bar(ticker, session, sessions, move))
    return tuple(rows)


def _bar(ticker: str, session: int, sessions: int, move: float) -> OHLCVBar:
    open_ = 100.0
    close = open_ * (1 + move)
    return OHLCVBar(
        ticker=ticker,
        bar_date=TODAY - timedelta(days=sessions - 1 - session),
        open=open_,
        high=max(open_, close) * 1.002,
        low=min(open_, close) * 0.998,
        close=close,
        volume=1_000_000,
    )
