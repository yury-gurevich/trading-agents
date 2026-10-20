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
from contracts.provider import RUN_REQUEST_LABEL
from contracts.run_posture import RUN_POSTURE_DEGRADED, RUN_POSTURE_NORMAL
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
# DL-309: the last placing fire leaves a run 20 minutes before the 23:30 window end.
_ACT_BY = time(23, 10)
_TICK_MINUTES = 10  # The pack's */10 cron; a fire lands seconds after its tick.


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


def fire_tick(now: datetime) -> time:
    """Return the cron tick a fire belongs to: its time floored to ten minutes."""
    return time(now.hour, now.minute - now.minute % _TICK_MINUTES)


def is_action_time(now: datetime) -> bool:
    """Return whether a dispatcher fire may place a run in the fleet window."""
    return _ACTION_START <= fire_tick(now) <= _ACT_BY


def outside_window(
    run_id: str, now: datetime, hold: Node | None
) -> ScheduledDispatchResult:
    """Keep an existing hold, or skip, naming which side of the window the fire is."""
    side = "before" if fire_tick(now) < _ACTION_START else "after"
    reason = f"{side} the placing window, {_ACTION_START:%H:%M} to {_ACT_BY:%H:%M} UTC"
    if hold is None:
        return ScheduledDispatchResult("skipped", run_id, reason)
    failures = tuple(str(item) for item in hold.props.get("failures", ()))
    return ScheduledDispatchResult("held", run_id, reason, hold.key, failures=failures)


def already_placed(graph: GraphStore, run_id: str) -> ScheduledDispatchResult | None:
    """Return the day's run an earlier fire placed, or None while there is none."""
    node = graph.get_node(RUN_REQUEST_LABEL, f"run-request:{run_id}")
    if node is None:
        return None
    degraded = node.props.get("run_posture") == RUN_POSTURE_DEGRADED
    return ScheduledDispatchResult(
        "already-placed",
        run_id,
        "placed by an earlier fire",
        node.key,
        tuple(str(ticker) for ticker in node.props.get("tickers", ())),
        failures=tuple(str(item) for item in node.props.get("degraded_by", ()))
        if degraded
        else (),
        run_posture=RUN_POSTURE_DEGRADED if degraded else RUN_POSTURE_NORMAL,
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
