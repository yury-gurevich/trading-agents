"""Dashboard wake windows follow the deploy script's cron weekdays.

Agent: surfaces
Role: prove weekday skips, start-day attribution, parsing and deployed defaults.
External I/O: reads the committed deploy script only.
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from surfaces.dashboard.settings import DashboardSettings
from surfaces.dashboard.time_windows import latest_window, next_master_wake, run_window
from surfaces.tests.test_dashboard_costs import _settings


@pytest.mark.parametrize(
    ("now", "expected_day"),
    [
        ("2026-09-25T00:45:00+00:00", "2026-09-25"),
        ("2026-09-25T12:00:00+00:00", "2026-09-25"),
        ("2026-09-26T00:45:00+00:00", "2026-09-28"),
        ("2026-09-26T12:00:00+00:00", "2026-09-28"),
        ("2026-09-26T21:00:00+00:00", "2026-09-28"),
        ("2026-09-27T21:00:00+00:00", "2026-09-28"),
        ("2026-09-28T12:00:00+00:00", "2026-09-28"),
    ],
)
def test_next_wake_is_the_next_weekdays_start(now: str, expected_day: str) -> None:
    """W1: a closed weekday window next opens at the next allowed 20:25 UTC."""
    settings = _settings().model_copy(update={"window_days_utc": "1-5"})
    assert next_master_wake(settings, datetime.fromisoformat(now)) == (
        f"{expected_day}T20:25:00+00:00"
    )


def test_master_is_awake_only_inside_a_weekday_window() -> None:
    """W2: Saturday's early hours belong to Friday's crossing-midnight window."""
    settings = _settings().model_copy(update={"window_days_utc": "1-5"})
    assert next_master_wake(settings, datetime(2026, 9, 25, 21, tzinfo=UTC)) is None
    assert next_master_wake(settings, datetime(2026, 9, 26, 0, 10, tzinfo=UTC)) is None
    assert next_master_wake(settings, datetime(2026, 9, 26, 21, tzinfo=UTC)) is not None


@pytest.mark.parametrize(
    ("now", "expected_day"),
    [
        ("2026-09-25T21:00:00+00:00", "2026-09-25"),
        ("2026-09-26T12:00:00+00:00", "2026-09-25"),
        ("2026-09-27T23:00:00+00:00", "2026-09-25"),
        ("2026-09-28T10:00:00+00:00", "2026-09-25"),
        ("2026-09-28T21:00:00+00:00", "2026-09-28"),
    ],
)
def test_latest_window_is_the_latest_weekday_one(now: str, expected_day: str) -> None:
    """W3: logs select the latest window's start day, including Monday morning."""
    settings = _settings().model_copy(update={"window_days_utc": "1-5"})
    start, _ = latest_window(settings, datetime.fromisoformat(now))
    assert start == datetime.fromisoformat(f"{expected_day}T20:25:00+00:00")


def test_star_opens_the_window_every_day() -> None:
    """W4: an explicit daily field keeps Saturday wakes and Sunday log windows."""
    settings = _settings().model_copy(update={"window_days_utc": "*"})
    assert next_master_wake(settings, datetime(2026, 9, 26, 12, tzinfo=UTC)) == (
        "2026-09-26T20:25:00+00:00"
    )
    start, _ = latest_window(settings, datetime(2026, 9, 27, 23, tzinfo=UTC))
    assert start == datetime(2026, 9, 27, 20, 25, tzinfo=UTC)


@pytest.mark.parametrize(
    ("days", "expected_day"),
    [
        ("6", "2026-09-26"),
        ("0", "2026-09-27"),
        ("7", "2026-09-27"),
        ("1,3", "2026-09-28"),
        ("2-4,6", "2026-09-26"),
        ("3", "2026-09-30"),
    ],
)
def test_weekday_field_is_read_as_cron_reads_it(days: str, expected_day: str) -> None:
    """W5: singles, lists and ranges use cron numbering, with both Sunday aliases."""
    settings = _settings().model_copy(update={"window_days_utc": days})
    assert next_master_wake(settings, datetime(2026, 9, 26, 12, tzinfo=UTC)) == (
        f"{expected_day}T20:25:00+00:00"
    )


@pytest.mark.parametrize("days", ["", "8", "5-1", "mon", "1-9", "1,", "-1", "1-"])
def test_unreadable_weekday_field_is_an_error(days: str) -> None:
    """W6: both helpers refuse malformed fields, including a range with no end."""
    settings = _settings().model_copy(update={"window_days_utc": days})
    now = datetime(2026, 9, 26, 12, tzinfo=UTC)
    with pytest.raises(ValueError, match="expected cron days 0-7"):
        next_master_wake(settings, now)
    with pytest.raises(ValueError, match="expected cron days 0-7"):
        latest_window(settings, now)


def test_defaults_are_the_deployed_windows() -> None:
    """W7: real defaults share all three script weekdays and end on the start day."""
    script = (Path(__file__).parents[2] / "infra" / "deploy-agents.ps1").read_text(
        encoding="utf-8"
    )
    params = dict(re.findall(r"\[string\]\$(\w+) = '([^']*)'", script))
    defaults = DashboardSettings(_env_file=None)
    weekdays = {
        params[name].split()[4]
        for name in ("MasterScaleStart", "AgentScaleStart", "ScaleEnd")
    }
    assert weekdays == {defaults.window_days_utc} == {"1-5"}
    assert defaults.window_end_utc == "23:30"
    start, end = run_window("2026-09-25", defaults)
    assert start == datetime(2026, 9, 25, 20, 25, tzinfo=UTC)
    assert end == datetime(2026, 9, 25, 23, 30, tzinfo=UTC)
    assert start.date() == end.date() == date(2026, 9, 25)
