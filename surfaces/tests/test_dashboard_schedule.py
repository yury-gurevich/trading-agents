"""Dashboard schedule tests, pinned to the deploy script and the dispatcher.

Agent: surfaces
Role: prove the dashboard's schedule facts match their sources and the calendar.
External I/O: reads the committed deploy script only; Azure reads are fakes.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest

from orchestration.scheduled_dispatch_actions import _ACTION_START
from surfaces.dashboard.projections_fleet import fleet_projection
from surfaces.dashboard.settings import DashboardSettings
from surfaces.dashboard.time_windows import next_fire, scheduled_execution
from surfaces.tests.dashboard_fakes import FakeAzureReader
from surfaces.tests.test_dashboard_costs import _settings
from surfaces.tests.test_dashboard_fleet import _graph

if TYPE_CHECKING:
    from surfaces.dashboard.azure_port import AzureRow

_DEPLOY = Path(__file__).parents[2] / "infra" / "deploy-agents.ps1"


def test_schedule_defaults_are_the_deployed_schedule() -> None:
    """A copied window that drifts from the deploy script misplaces the log views."""
    script = _DEPLOY.read_text(encoding="utf-8")
    params = dict(re.findall(r"\[string\]\$(\w+) = '([^']*)'", script))

    assert params["ScaleTimezone"] == "UTC"
    assert _default("master_window_start_utc") == _hh_mm(params["MasterScaleStart"])
    assert _default("agent_window_start_utc") == _hh_mm(params["AgentScaleStart"])
    assert _default("window_end_utc") == _hh_mm(params["ScaleEnd"])
    assert _default("dispatcher_fire_utc") == f"{_ACTION_START:%H:%M}"


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        (datetime(2026, 12, 24, 12, tzinfo=UTC), "2026-12-24T22:30:00+00:00"),
        (datetime(2026, 12, 24, 23, tzinfo=UTC), "2026-12-28T22:30:00+00:00"),
        (datetime(2027, 12, 31, 23, tzinfo=UTC), None),
    ],
)
def test_next_fire_skips_weekends_and_holidays(
    now: datetime, expected: str | None
) -> None:
    """Christmas Friday and the weekend after it place no run, so none is promised."""
    assert next_fire(_settings(), now) == expected


def test_the_placing_tick_is_the_first_at_or_after_the_fire_time() -> None:
    # The live ticker: 22:00 to 23:50 every ten minutes, plus the next day's first.
    day = [
        f"2026-09-22T{hour}:{tens}0:00+00:00"
        for hour in ("22", "23")
        for tens in "012345"
    ]
    rows = _ticks(*day, "2026-09-23T22:00:00+00:00")

    assert _start(scheduled_execution(rows, "2026-09-22", _settings())) == (
        "2026-09-22T22:30:00+00:00"
    )


def test_without_a_due_tick_the_day_then_the_latest_tick_is_shown() -> None:
    settings = _settings()
    early = _ticks("2026-09-22T22:00:00+00:00", "2026-09-22T22:10:00+00:00")
    other_day = _ticks("2026-09-21T22:30:00+00:00")

    assert _start(scheduled_execution(early, "2026-09-22", settings)) == (
        "2026-09-22T22:10:00+00:00"
    )
    assert scheduled_execution(other_day, "2026-09-22", settings) == other_day[0]
    assert scheduled_execution([], "2026-09-22", settings) is None


class _TickerReader(FakeAzureReader):
    def list_job_executions(self, job: str) -> list[AzureRow]:
        del job
        return _ticks(
            "2026-07-09T22:20:00Z", "2026-07-09T22:30:00Z", "2026-07-09T23:50:00Z"
        )


def test_fleet_cron_row_shows_the_placing_tick_not_the_days_last() -> None:
    result = fleet_projection(_graph(), _TickerReader(), _settings(), "fleet")
    cron = cast("list[dict[str, str]]", result["stages"])[0]

    assert cron["detail"].startswith("2026-07-09T22:30")
    assert cron["status"] == "good"


def _default(field: str) -> str:
    return str(DashboardSettings.model_fields[field].default)


def _hh_mm(cron: str) -> str:
    minute, hour = cron.split()[:2]
    return f"{int(hour):02}:{int(minute):02}"


def _ticks(*stamps: str) -> list[AzureRow]:
    """Azure lists newest first; every tick succeeds, whether it placed or not."""
    return [
        {
            "name": f"dispatcher-cron-{index}",
            "status": "Succeeded",
            "start_time": stamp,
            "end_time": stamp,
            "image": "ghcr.io/org/dispatcher:s225",
        }
        for index, stamp in enumerate(sorted(stamps, reverse=True))
    ]


def _start(row: AzureRow | None) -> str:
    assert row is not None
    return str(row["start_time"])
