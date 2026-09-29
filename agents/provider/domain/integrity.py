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

from agents.provider.domain.market_calendar import trading_sessions_between
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
    # An extreme NEWEST bar is attributed to its OWN ticker and that ticker is
    # EXCLUDED — a partial degradation (DRIFT-014), not a whole-batch fallback. At
    # S&P-500 scale one >Nsigma name must not reject the clean survivors; the batch
    # note tainted everything. An older bar is never re-judged (DL-247). Staleness is
    # measured on the pre-exclusion bars so an excluded anomalous name is not
    # double-counted as missing.
    anomalous = _anomalous_tickers(valid, settings)
    stale = _stale_tickers(tickers, valid, window.end, settings.max_staleness_days)
    if stale:
        notes.append("stale_or_missing_tickers")
    delivered = [bar for bar in valid if bar.ticker not in anomalous]
    returned_tickers = {bar.ticker for bar in delivered}
    returned = sum(1 for ticker in tickers if ticker in returned_tickers)
    quality = DataQualityTrace(
        requested=len(tickers),
        returned=returned,
        # A per-ticker exclusion does not taint the delivery; only a genuine
        # whole-batch failure does (a tainting note, or nothing left to score).
        used_fallback=bool(notes) or returned == 0,
        stale_tickers=tuple(sorted(stale)),
        anomalous_tickers=tuple(sorted(anomalous)),
        notes=tuple(dict.fromkeys(notes)),
    )
    return tuple(delivered), quality


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


def _anomalous_tickers(bars: list[OHLCVBar], settings: ProviderSettings) -> set[str]:
    """Tickers whose NEWEST bar is an extreme open-to-close move (PROV-OUT-09).

    The detector is deliberately pooled: a >Nsigma move against every ticker's move
    on the same session is a data-integrity flag, not a per-stock vol filter.
    DRIFT-014 made the consequence per-ticker (the caller excludes the outlier).
    DL-247 narrows the scope: only each ticker's own last bar is judged, against
    that session's cross-section, so a real extreme day in its history never drops
    it. The pool cannot put one move beyond sqrt(n - 1) sigma (DRIFT-090).
    """
    sessions: dict[date, list[tuple[str, float]]] = {}
    newest: dict[str, date] = {}
    for bar in bars:  # validated: every price finite and > 0 (_valid_bar)
        move = (bar.close - bar.open) / bar.open
        sessions.setdefault(bar.bar_date, []).append((bar.ticker, move))
        newest[bar.ticker] = max(newest.get(bar.ticker, date.min), bar.bar_date)
    return {
        ticker
        for day in set(newest.values())
        for ticker in _outliers(sessions[day], settings.max_daily_move_sigma)
        if newest[ticker] == day
    }


def _outliers(moves: list[tuple[str, float]], max_sigma: float) -> set[str]:
    """Tickers beyond ``max_sigma`` of one session's pooled moves; <2 abstains."""
    if len(moves) < 2:
        return set()
    returns = [value for _, value in moves]
    sigma = pstdev(returns)
    if sigma == 0:
        return set()
    center = mean(returns)
    limit = max_sigma * sigma
    return {ticker for ticker, value in moves if abs(value - center) > limit}


def _stale_tickers(
    tickers: tuple[str, ...],
    bars: list[OHLCVBar],
    end: date,
    max_staleness_days: int,
) -> set[str]:
    latest: dict[str, date] = {}
    for bar in bars:
        latest[bar.ticker] = max(latest.get(bar.ticker, date.min), bar.bar_date)
    # Staleness is measured in TRADING SESSIONS, not calendar days, so a weekend or
    # market holiday does not flag current data as stale (DL-10).
    return {
        ticker
        for ticker in tickers
        if ticker not in latest
        or trading_sessions_between(latest[ticker], end) > max_staleness_days
    }
