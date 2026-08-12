"""Run-request history-window derivation.

Agent: orchestration
Role: convert analyst-declared bar requirements into RunRequest calendar windows.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING

from agents.analyst.history_requirements import required_history_bars
from agents.provider.domain.market_calendar import is_trading_session

if TYPE_CHECKING:
    from agents.analyst.settings import AnalystSettings


def declared_lookback_days(
    settings: AnalystSettings,
    *,
    as_of: date | None = None,
    staleness_buffer_sessions: int = 0,
) -> int:
    """Return calendar days that cover the largest declared indicator history."""
    end = as_of or datetime.now(tz=UTC).date()
    required_days = calendar_days_for_sessions(
        required_history_bars(settings) + staleness_buffer_sessions, end
    )
    return max(settings.lookback_days, required_days)


def calendar_days_for_sessions(required_bars: int, as_of: date) -> int:
    """Return a calendar-day lookback that contains *required_bars* sessions."""
    if required_bars < 1:
        raise ValueError("required_bars must be positive")
    start = as_of
    sessions = 0
    while sessions < required_bars:
        if is_trading_session(start):
            sessions += 1
        if sessions < required_bars:
            start -= timedelta(days=1)
    return max(1, (as_of - start).days)
