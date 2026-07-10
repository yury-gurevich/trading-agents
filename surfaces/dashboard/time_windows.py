"""UTC scale-window helpers for dashboard logs and next-fire vitals.

Agent: surfaces
Role: derive run-scoped and latest fleet windows from deployment-aligned settings.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from surfaces.dashboard.settings import DashboardSettings


def run_window(run_day: str, settings: DashboardSettings) -> tuple[datetime, datetime]:
    """Return the master-start through scale-end UTC window for one run day."""
    day = date.fromisoformat(run_day)
    start = datetime.combine(day, _time(settings.master_window_start_utc), UTC)
    end = datetime.combine(day, _time(settings.window_end_utc), UTC)
    if end <= start:
        end += timedelta(days=1)
    return start, end


def latest_window(
    settings: DashboardSettings, now: datetime | None = None
) -> tuple[datetime, datetime]:
    """Return the current daily window if started, otherwise the previous one."""
    current = now or datetime.now(tz=UTC)
    today_start = datetime.combine(
        current.date(), _time(settings.master_window_start_utc), UTC
    )
    day = (
        current.date() if current >= today_start else current.date() - timedelta(days=1)
    )
    return run_window(day.isoformat(), settings)


def next_fire(settings: DashboardSettings, now: datetime | None = None) -> str:
    """Return the next dispatcher fire as an ISO UTC timestamp."""
    current = now or datetime.now(tz=UTC)
    fire = datetime.combine(current.date(), _time(settings.dispatcher_fire_utc), UTC)
    if fire <= current:
        fire += timedelta(days=1)
    return fire.isoformat()


def window_label(settings: DashboardSettings) -> str:
    """Render the deployed master-start through scale-end interval."""
    return f"{settings.master_window_start_utc}-{settings.window_end_utc} UTC"


def _time(value: str) -> time:
    try:
        parsed = time.fromisoformat(value)
    except ValueError:
        raise ValueError(f"invalid UTC time {value!r}; expected HH:MM") from None
    if parsed.tzinfo is not None or parsed.second or parsed.microsecond:
        raise ValueError(f"invalid UTC time {value!r}; expected HH:MM")
    return parsed
