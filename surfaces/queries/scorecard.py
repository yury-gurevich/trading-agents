"""The unattended scorecard: G1, G3 and two clocks over a window of scheduled sessions.

Agent: surfaces
Role: count complete sessions and the human actions placed between runs.
External I/O: injected GraphStore reads only; no agent request and no model call.

Each session's word is the acceptance gate's (`scorecard_verdicts`); nothing here judges
a run. An action belongs to the first counted session placed at or after it, and after
the previous session's placement, so a weekend action counts against Monday's run (S236
Scope 5, DL-235 decision 5); a hold answer belongs to the session whose run it names.
The window is dates, never the selected run (SRF-OUT-08). When every session in it holds
and the clocks' target is longer than the window, the clocks read earlier sessions too
(DL-235 amendment): a 30-day window holds 18-23 sessions, and 20 is the target.
"""

from __future__ import annotations

from bisect import bisect_left
from collections import Counter
from dataclasses import replace
from datetime import UTC, date, datetime, time, timedelta
from typing import TYPE_CHECKING

from contracts.provider import RUN_REQUEST_LABEL
from orchestration.daily_brief import LAST_FIRE
from orchestration.scheduled_dispatch import ProviderTradingCalendar, scheduled_run_id
from surfaces.queries.scorecard_actions import human_actions, instant
from surfaces.queries.scorecard_model import Scorecard, SessionRow
from surfaces.queries.scorecard_verdicts import PROCESS_VERDICTS, session_word

if TYPE_CHECKING:
    from kernel import GraphStore, Node
    from surfaces.queries.scorecard_verdicts import VerdictMemo
    from surfaces.scorecard_settings import ScorecardSettings

_CALENDAR = ProviderTradingCalendar()
_NOTHING_CLOSED = "no scheduled session in the window has closed yet"


def scorecard(
    graph: GraphStore,
    *,
    now: datetime,
    settings: ScorecardSettings,
    verdicts: VerdictMemo | None = None,
) -> Scorecard:
    """Score the window ending ``now``; ``verdicts`` defaults to the process memo."""
    days = counted_days(now, settings.scorecard_window_days)
    if not days:
        return Scorecard("unavailable", settings, reason=_NOTHING_CLOSED)
    memo = PROCESS_VERDICTS if verdicts is None else verdicts
    tick = time.fromisoformat(settings.dispatcher_fire_utc)
    rows = _rows(graph, days, tick, memo)
    card = Scorecard("measured", settings, rows)
    short = settings.scorecard_clock_sessions - card.counted
    if short > 0 and card.unattended == card.counted:
        earlier = _rows(graph, _sessions_before(days[0], short), tick, memo)
        card = replace(card, streak=earlier + rows)
    return card


def _rows(
    graph: GraphStore, days: tuple[date, ...], tick: time, memo: VerdictMemo
) -> tuple[SessionRow, ...]:
    """One row per session: the gate's word and the actions placed on it."""
    before = _previous_session(days[0])
    requests = {day: _request(graph, day) for day in (before, *days)}
    placed = [_placement(requests[day], day, tick) for day in days]
    opened = _placement(requests[before], before, tick)
    named = {scheduled_run_id(day): day for day in days}
    kinds: dict[date, Counter[str]] = {day: Counter() for day in days}
    for action in human_actions(graph, tick):
        day = named.get(action.run_id) or _placed_on(action.at, placed, opened, days)
        if day is not None:
            kinds[day][action.kind] += 1
    return tuple(
        SessionRow(
            day,
            scheduled_run_id(day),
            session_word(graph, scheduled_run_id(day), requests[day], memo),
            dict(sorted(kinds[day].items())),
        )
        for day in days
    )


def counted_days(now: datetime, window_days: int) -> tuple[date, ...]:
    """Sessions dated ``window_days`` before today through today whose window closed."""
    today = now.astimezone(UTC).date()
    dates = (today - timedelta(days=back) for back in range(window_days, -1, -1))
    return tuple(
        day
        for day in dates
        if _CALENDAR.is_trading_session(day)
        and now >= datetime.combine(day, LAST_FIRE, UTC)
    )


def _sessions_before(day: date, count: int) -> tuple[date, ...]:
    """The ``count`` sessions before ``day``, oldest first."""
    found: list[date] = []
    while len(found) < count:
        day = _previous_session(day)
        found.append(day)
    return tuple(reversed(found))


def _previous_session(day: date) -> date:
    before = day - timedelta(days=1)
    while not _CALENDAR.is_trading_session(before):
        before -= timedelta(days=1)
    return before


def _request(graph: GraphStore, day: date) -> Node | None:
    return graph.get_node(RUN_REQUEST_LABEL, f"run-request:{scheduled_run_id(day)}")


def _placement(request: Node | None, day: date, tick: time) -> datetime:
    """When the session's run was placed: its `requested_at`, else the tick that day."""
    stored = request.props.get("requested_at") if request is not None else None
    if stored is None:
        return datetime.combine(day, tick, UTC)
    return instant(stored, tick, label="RunRequest")


def _placed_on(
    at: datetime, placed: list[datetime], opened: datetime, days: tuple[date, ...]
) -> date | None:
    """The first counted session placed at or after ``at``, when ``at`` is in window."""
    index = bisect_left(placed, at)
    return days[index] if opened < at and index < len(days) else None
