"""Placement actions and time boundaries for answer-aware scheduled dispatch.

Agent: orchestration
Role: preserve the ready-run path and bound human override placement.
External I/O: reads and writes the injected GraphStore.
"""

from __future__ import annotations

from datetime import UTC, datetime, time
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from agents.scanner.universe import FileUniverse
from orchestration.scheduled_dispatch import (
    ScheduledDispatchResult,
    place_scheduled_run,
)
from orchestration.settings import OrchestratorSettings
from orchestration.start import place_run_request

if TYPE_CHECKING:
    from datetime import date

    from agents.scanner.universe import UniverseSource
    from kernel import GraphStore, Node
    from orchestration.scheduled_dispatch import TradingCalendar

_ACTION_START = time(22, 30)
_ACT_BY = time(23, 20)


def act_by_text(now: datetime, timezone: str) -> str:
    """Name the answer deadline in the operator's time first, UTC second.

    A runtime image without zone data still gets a correct UTC deadline.
    """
    utc = f"{_ACT_BY:%H:%M} UTC"
    try:
        zone = ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError):
        return utc
    deadline = datetime.combine(now.date(), _ACT_BY, UTC).astimezone(zone)
    return f"{deadline:%H:%M} {timezone.rsplit('/', 1)[-1]} ({utc})"


def is_action_time(now: datetime) -> bool:
    """Return whether a dispatcher fire may place a run in the fleet window."""
    return _ACTION_START <= now.time().replace(tzinfo=None) <= _ACT_BY


def outside_window(
    run_id: str, reason: str, hold: Node | None
) -> ScheduledDispatchResult:
    """Keep an existing hold, or skip placement outside the bounded window."""
    return ScheduledDispatchResult(
        "held" if hold is not None else "skipped", run_id, reason
    )


def place_override(
    graph: GraphStore,
    *,
    run_id: str,
    as_of: date,
    reason: str,
    settings: OrchestratorSettings | None,
    universe_source: UniverseSource | None,
) -> ScheduledDispatchResult:
    """Place the normal day-keyed run despite a failed readiness check."""
    active_settings = settings or OrchestratorSettings()
    tickers = (universe_source or FileUniverse()).members(active_settings.universe)
    if not tickers:
        raise ValueError(f"universe {active_settings.universe!r} has no tickers")
    node = place_run_request(graph, run_id=run_id, tickers=tickers, as_of=as_of)
    return ScheduledDispatchResult("placed", run_id, reason, node.key, tickers)


def place_scheduled(
    graph: GraphStore,
    *,
    as_of: date,
    now: datetime,
    calendar: TradingCalendar | None,
    settings: OrchestratorSettings | None,
    universe_source: UniverseSource | None,
) -> ScheduledDispatchResult:
    """Call the unchanged scheduled placement path with an optional calendar."""
    if calendar is not None:
        return place_scheduled_run(
            graph,
            as_of=as_of,
            calendar=calendar,
            settings=settings,
            universe_source=universe_source,
            now=now,
        )
    return place_scheduled_run(
        graph, as_of=as_of, settings=settings, universe_source=universe_source, now=now
    )
