"""Deterministic synthetic daily bars with a chosen shape (no randomness: same case, same bytes)."""

from __future__ import annotations

import math
from datetime import date, timedelta

from contracts.provider import OHLCVBar

END = date(2026, 9, 30)


def trading_days(n: int, end: date = END) -> list[date]:
    """The last n weekdays up to `end` (holidays ignored: synthetic)."""
    out: list[date] = []
    d = end
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d -= timedelta(days=1)
    return out[::-1]


def bars(
    ticker: str,
    segments: list[tuple[int, float]],
    *,
    start: float = 100.0,
    wiggle: float = 0.006,
    phase: float = 0.0,
    volume: int = 3_000_000,
    n: int = 300,
    period: float = 2.7,
) -> tuple[OHLCVBar, ...]:
    """Piecewise drift: segments = [(sessions, daily_drift), ...]; the last segments end on END."""
    drifts: list[float] = []
    for sessions, drift in segments:
        drifts.extend([drift] * sessions)
    drifts = ([segments[0][1]] * max(0, n - len(drifts)) + drifts)[-n:]
    days = trading_days(n)
    price, out = start, []
    for i, (day, drift) in enumerate(zip(days, drifts, strict=True)):
        prev = price
        price *= 1 + drift + wiggle * math.sin(i / period + phase)
        hi, lo = max(prev, price) * 1.006, min(prev, price) * 0.994
        out.append(
            OHLCVBar(
                ticker=ticker,
                bar_date=day,
                open=round(prev, 4),
                high=round(hi, 4),
                low=round(lo, 4),
                close=round(price, 4),
                volume=volume + (i % 7) * 25_000,
            )
        )
    return tuple(out)
