"""S250 finding: before 2024 the declared window holds fewer sessions than the bar.

Agent: tooling
Role: pin the provider calendar's pre-2024 gap so the rule's hazard stays visible.
External I/O: local tmp files only.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from scripts.replay_settings import build_effective_settings
from tests.replay_history_fixtures import (
    COUNTER,
    NYSE_CLOSURES_2019,
    observe,
    run_window,
    write_cache,
)

from agents.analyst.history_requirements import required_history_bars
from orchestration.history_window import declared_lookback_days

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_before_2024_the_declared_window_holds_fewer_sessions_than_the_bar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """S250 finding (DL-258) / PROV-TRG-05: pinned; it flips when the calendar is.

    The provider's calendar lists NYSE closures for 2024-2027 only, so before 2024
    `declared_lookback_days` counts every weekday as a session and the window it
    builds holds 203 weekdays, not 203 sessions. On a cache whose sessions skip
    2019's real closures, a line with a bar on every session holds 197 bars on
    2019-12-31 and the rule withholds it. Measured on the real calendar: 194-198 on
    every session of 2017-2023. Until the calendar is extended, a replay with the
    rule on offers no unheld line before 2024 (Return notes, S250).
    """
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
    assert in_window == 197 < required_history_bars(settings.analyst)
    assert seen == [(sessions[last], (), frozenset())]
    assert summary["absent_inputs"][COUNTER] == 1
