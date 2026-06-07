"""Market-data integrity checks for provider payloads.

Agent: provider
Role: filter invalid OHLCV bars and produce honest data-quality traces.
External I/O: none.
"""

from __future__ import annotations

import math
from datetime import date
from statistics import mean, pstdev
from typing import TYPE_CHECKING

from contracts.provider import DataQualityTrace, OHLCVBar

if TYPE_CHECKING:
    from agents.provider.settings import ProviderSettings
    from contracts.common import Window


def validate_bars(
    tickers: tuple[str, ...],
    bars: tuple[OHLCVBar, ...],
    window: Window,
    settings: ProviderSettings,
) -> tuple[tuple[OHLCVBar, ...], DataQualityTrace]:
    """Filter invalid bars and summarize data quality."""
    notes: list[str] = []
    valid = [bar for bar in bars if _valid_bar(bar, notes)]
    notes.extend(_daily_move_notes(valid, settings))
    stale = _stale_tickers(tickers, valid, window.end, settings.max_staleness_days)
    if stale:
        notes.append("stale_or_missing_tickers")
    returned_tickers = {bar.ticker for bar in valid}
    returned = sum(1 for ticker in tickers if ticker in returned_tickers)
    quality = DataQualityTrace(
        requested=len(tickers),
        returned=returned,
        used_fallback=bool(notes),
        stale_tickers=tuple(sorted(stale)),
        notes=tuple(dict.fromkeys(notes)),
    )
    return tuple(valid), quality


def degraded_quality(
    tickers: tuple[str, ...], *, note: str = "source_unavailable"
) -> DataQualityTrace:
    """Return a first-class degraded trace when a source cannot provide data."""
    return DataQualityTrace(
        requested=len(tickers),
        returned=0,
        used_fallback=True,
        stale_tickers=tuple(sorted(tickers)),
        notes=(note,),
    )


def _valid_bar(bar: OHLCVBar, notes: list[str]) -> bool:
    values = (bar.open, bar.high, bar.low, bar.close)
    if any(not math.isfinite(value) for value in values):
        notes.append("non_finite_price_rejected")
        return False
    if bar.volume < 0 or min(values) <= 0:
        notes.append("invalid_ohlcv_rejected")
        return False
    if bar.high < max(bar.open, bar.close) or bar.low > min(bar.open, bar.close):
        notes.append("inconsistent_ohlcv_rejected")
        return False
    return True


def _daily_move_notes(
    bars: list[OHLCVBar], settings: ProviderSettings
) -> tuple[str, ...]:
    returns = [
        (bar.close - bar.open) / bar.open
        for bar in bars
        if bar.open > 0 and math.isfinite((bar.close - bar.open) / bar.open)
    ]
    if len(returns) < 2:
        return ()
    sigma = pstdev(returns)
    if sigma == 0:
        return ()
    center = mean(returns)
    limit = settings.max_daily_move_sigma * sigma
    if any(abs(value - center) > limit for value in returns):
        return ("daily_move_sigma_anomaly",)
    return ()


def _stale_tickers(
    tickers: tuple[str, ...],
    bars: list[OHLCVBar],
    end: date,
    max_staleness_days: int,
) -> set[str]:
    latest: dict[str, date] = {}
    for bar in bars:
        latest[bar.ticker] = max(latest.get(bar.ticker, date.min), bar.bar_date)
    return {
        ticker
        for ticker in tickers
        if ticker not in latest or (end - latest[ticker]).days > max_staleness_days
    }
