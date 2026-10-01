"""S250 return 1: with the calendar repaired, the declared window holds the bar.

Agent: tooling
Role: prove the harness consequence of the 2016-2023 holiday table (DL-258
      amendment): every session's declared window holds the analyst's required bars,
      and a line with a bar on every session is no longer withheld before 2024.
External I/O: local tmp files only.

This file flipped in S250 return 1. It used to pin the gap: with closures listed for
2024-2027 only, the window before 2024 held 203 weekdays, not 203 sessions, and a
full line on 2019-12-31 held 197 bars and was withheld. It now asserts the repair.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

from scripts.replay_settings import build_effective_settings
from tests.replay_history_fixtures import (
    COUNTER,
    NYSE_CLOSURES_2019,
    WINDOW_SESSIONS,
    observe,
    run_window,
    write_cache,
)

from agents.analyst.history_requirements import required_history_bars
from agents.analyst.settings import AnalystSettings
from agents.provider.domain.market_calendar import (
    is_trading_session,
    trading_sessions_between,
)
from orchestration.history_window import declared_lookback_days

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_every_sessions_declared_window_holds_the_required_bars() -> None:
    """S250 return 1 (DL-258) / PROV-TRG-05: from 2017-01-03 to 2026-09-25, on
    every session the calendar names, the window `declared_lookback_days` gives
    holds at least `required_history_bars` sessions (exactly 200 plus the 3-session
    staleness buffer, 203), so the history rule never starves a full line."""
    analyst = AnalystSettings()
    required = required_history_bars(analyst)
    buffer = build_effective_settings(()).provider.max_staleness_days
    short: list[date] = []
    day, checked = date(2017, 1, 3), 0
    while day <= date(2026, 9, 25):
        if is_trading_session(day):
            lookback = declared_lookback_days(
                analyst, as_of=day, staleness_buffer_sessions=buffer
            )
            start = day - timedelta(days=lookback)
            held = trading_sessions_between(start - timedelta(days=1), day)
            checked += 1
            if held < required or held != required + buffer:
                short.append(day)
        day += timedelta(days=1)

    assert required + buffer == WINDOW_SESSIONS
    assert checked == 2_446
    assert short == []


def test_a_full_line_is_offered_on_2019_12_31(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """S250 return 1 (DL-258) / PROV-TRG-05: on a cache whose sessions skip 2019's
    real closures (now the calendar's own), a line with a bar on every session holds
    203 bars in the declared window and the rule offers it; nothing is withheld."""
    sessions = write_cache(
        tmp_path / "cache", {"LONG": range(252)}, closures=NYSE_CLOSURES_2019
    )
    assert len(sessions) == 252
    seen = observe(monkeypatch)
    last = len(sessions) - 1
    settings = build_effective_settings(())

    summary = run_window(
        tmp_path / "cache",
        tmp_path / "out",
        sessions,
        start=last,
        end=last,
        require_history=True,
    )

    lookback = declared_lookback_days(
        settings.analyst,
        as_of=sessions[last],
        staleness_buffer_sessions=settings.provider.max_staleness_days,
    )
    in_window = sum(
        1 for day in sessions if sessions[last] - timedelta(days=lookback) <= day
    )
    assert in_window == WINDOW_SESSIONS >= required_history_bars(settings.analyst)
    assert seen == [(sessions[last], ("LONG",), frozenset({"LONG"}))]
    assert summary["absent_inputs"].get(COUNTER, 0) == 0
