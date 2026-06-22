"""Trading-session calendar tests (DL-10).

Agent: provider
Role: cover trading_sessions_between (weekend + holiday exclusion) and the staleness
      behavior — fresh data across a holiday weekend is not flagged stale.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

from agents.provider.domain.integrity import validate_bars
from agents.provider.domain.market_calendar import (
    _NYSE_HOLIDAYS,
    is_trading_session,
    trading_sessions_between,
)
from agents.provider.settings import ProviderSettings
from contracts.common import Window
from contracts.provider import OHLCVBar


def test_holidays_are_all_weekdays() -> None:
    """Observed NYSE closures are always weekdays (catches data-entry errors)."""
    assert all(d.weekday() < 5 for d in _NYSE_HOLIDAYS)


def test_is_trading_session_excludes_weekends_and_holidays() -> None:
    assert is_trading_session(date(2026, 6, 22)) is True  # Monday
    assert is_trading_session(date(2026, 6, 20)) is False  # Saturday
    assert is_trading_session(date(2026, 6, 19)) is False  # Juneteenth (Friday)


def test_trading_sessions_between_counts_sessions_not_calendar_days() -> None:
    # Thu Jun 18 -> Mon Jun 22: Fri = Juneteenth, Sat/Sun weekend => 1 session.
    assert trading_sessions_between(date(2026, 6, 18), date(2026, 6, 22)) == 1
    # same-day and future window-ends both yield zero sessions elapsed.
    assert trading_sessions_between(date(2026, 6, 22), date(2026, 6, 22)) == 0
    assert trading_sessions_between(date(2026, 6, 22), date(2026, 6, 18)) == 0


def test_fresh_data_across_holiday_weekend_is_not_stale() -> None:
    """DL-10: a Jun-18 close on Jun-22 (Juneteenth + weekend) is 1 session old.

    Under the old calendar-day count it was 4 > max_staleness_days(3) and the whole
    batch was flagged degraded, killing the analyst.
    """
    window = Window(start=date(2026, 5, 1), end=date(2026, 6, 22))
    bar = OHLCVBar(
        ticker="AAPL",
        bar_date=date(2026, 6, 18),
        open=100.0,
        high=102.0,
        low=99.0,
        close=101.0,
        volume=1000,
    )
    _bars, quality = validate_bars(("AAPL",), (bar,), window, ProviderSettings())
    assert quality.stale_tickers == ()
    assert quality.used_fallback is False
