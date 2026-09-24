"""UTC scale-window helpers for dashboard logs and next-fire vitals.

Agent: surfaces
Role: derive fleet windows, the next fire and the placing tick from the schedule.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from orchestration.scheduled_dispatch import ProviderTradingCalendar

if TYPE_CHECKING:
    from orchestration.scheduled_dispatch import TradingCalendar
    from surfaces.dashboard.azure_port import AzureRow
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


def next_fire(
    settings: DashboardSettings,
    now: datetime | None = None,
    calendar: TradingCalendar | None = None,
) -> str | None:
    """Return the next placing fire as an ISO UTC timestamp, sessions only.

    The cron ticks every weekday, but the dispatcher places a run only on a NYSE
    session, so weekends and holidays are skipped with its own calendar. None
    means past that calendar's end, where the dispatcher refuses to schedule.
    """
    current = now or datetime.now(tz=UTC)
    sessions = calendar or ProviderTradingCalendar()
    day = current.date()
    while day <= sessions.window_end():
        fire = datetime.combine(day, _time(settings.dispatcher_fire_utc), UTC)
        if fire > current and sessions.is_trading_session(day):
            return fire.isoformat()
        day += timedelta(days=1)
    return None


def scheduled_execution(
    rows: list[AzureRow], run_day: str, settings: DashboardSettings
) -> AzureRow | None:
    """Return the dispatcher tick that could place the run, not the day's last.

    The cron ticks every ten minutes and only ticks from the fire time on may
    place, so the earliest run-day tick at or after it placed (or held) the run.
    Without one: the run day's latest tick, then the latest tick of all.
    """
    fire = f"{run_day}T{_time(settings.dispatcher_fire_utc):%H:%M}"
    day = sorted(
        (row for row in rows if str(row.get("start_time", "")).startswith(run_day)),
        key=lambda row: str(row.get("start_time", "")),
    )
    due = [row for row in day if str(row.get("start_time", "")) >= fire]
    if due:
        return due[0]
    return day[-1] if day else (rows[0] if rows else None)


def next_master_wake(settings: DashboardSettings, now: datetime) -> str | None:
    """Return when the master next wakes, or None while it is awake.

    The master checks the fleet only inside its window, so outside it the next
    check is the next window's start, not "about an hour" away.
    """
    start, end = latest_window(settings, now)
    if start <= now < end:
        return None
    wake = datetime.combine(now.date(), _time(settings.master_window_start_utc), UTC)
    if wake <= now:
        wake += timedelta(days=1)
    return wake.isoformat()


def window_label(
    settings: DashboardSettings, start_utc: str, now: datetime | None = None
) -> str:
    """Render a UTC scale window in the operator's own time for today."""
    day = (now or datetime.now(tz=UTC)).date()
    zone = ZoneInfo(settings.operator_timezone)
    start = datetime.combine(day, _time(start_utc), UTC).astimezone(zone)
    end = datetime.combine(day, _time(settings.window_end_utc), UTC).astimezone(zone)
    return f"{start:%H:%M}-{end:%H:%M} {settings.operator_timezone.rsplit('/', 1)[-1]}"


def _time(value: str) -> time:
    try:
        parsed = time.fromisoformat(value)
    except ValueError:
        raise ValueError(f"invalid UTC time {value!r}; expected HH:MM") from None
    if parsed.tzinfo is not None or parsed.second or parsed.microsecond:
        raise ValueError(f"invalid UTC time {value!r}; expected HH:MM")
    return parsed
