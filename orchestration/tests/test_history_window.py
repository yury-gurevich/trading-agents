"""Run-request history-window derivation tests.

Agent: orchestration
Role: verify declared indicator bars become calendar windows with NYSE sessions.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

import pytest

from agents.analyst.history_requirements import required_history_bars
from agents.analyst.settings import AnalystSettings
from orchestration.history_window import (
    calendar_days_for_sessions,
    declared_lookback_days,
)


def test_calendar_days_for_sessions_rejects_zero_bars() -> None:
    """ANLZ-IDN-01: a declared indicator history requirement must be positive."""
    with pytest.raises(ValueError, match="required_bars"):
        calendar_days_for_sessions(0, date(2026, 8, 11))


def test_calendar_days_for_sessions_skips_non_sessions() -> None:
    """ANLZ-IDN-01: required bars are counted as market sessions, not days."""
    assert calendar_days_for_sessions(1, date(2026, 8, 8)) == 1


def test_declared_lookback_days_uses_default_clock() -> None:
    """ANLZ-IDN-01: default run requests still cover declared indicator bars."""
    settings = AnalystSettings()

    assert declared_lookback_days(settings) >= required_history_bars(settings)
