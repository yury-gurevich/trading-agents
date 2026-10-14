"""The container sensor: each dispatcher fire reads the platform's container events.

Agent: orchestration
Role: record new container events and tell the operator once of every alarm (DL-301).
External I/O: reads/writes the injected GraphStore; calls the injected log reader and
    the injected alarm port.

Imported only inside `container_sensor_guard`'s fault boundary, so neither this
module nor anything it imports can stop a dispatcher fire (`DSP-FAIL-04`).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, timedelta
from typing import TYPE_CHECKING, Protocol

from orchestration.container_alarm_text import alarm_message, group_events
from orchestration.container_events import ContainerEvent, classify
from orchestration.container_lines import LINE_WINDOW, choose_line
from orchestration.container_queries import EVENT_ROWS_MAX
from orchestration.container_sensor_graph import (
    CONTAINER_EVENT,
    READ_OK,
    SENSOR_READ,
    TOLD,
    event_props,
    last_read_until,
    read_key,
    read_window,
    untold_alarms,
)
from orchestration.daily_brief_fills import parse_instant

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime

    from kernel import GraphStore, Node
    from orchestration.container_logs import LogReader
    from orchestration.container_queries import Row
    from orchestration.settings import OrchestratorSettings

_Lines = dict[str, list[tuple["datetime", str]]]


class AlarmPort(Protocol):
    """The one operation the sensor needs of the operator's channel."""

    last_error: str

    def send_alarm(self, *, text: str) -> int | None:
        """Send one plain-text alarm; return its message id, or None on failure."""
        ...  # pragma: no cover - protocol declaration only.


@dataclass(frozen=True)
class SensorOutcome:
    """What one read found, recorded and told."""

    read_key: str
    rows: int
    recorded: int
    alarms: int
    told: int
    send_error: str


def sense_containers(
    graph: GraphStore,
    reader: LogReader,
    port: AlarmPort,
    *,
    now: datetime,
    settings: OrchestratorSettings,
) -> SensorOutcome:
    """Read the events since the last read, record the new ones, tell the untold."""
    until = now.astimezone(UTC)
    start, capped = read_window(last_read_until(graph), until, settings)
    rows = reader.events(start, until)
    events = _new_events(graph, rows)
    lines = _error_lines(reader, events, until)
    key = read_key(until)
    for event in events:
        why = _why(event, lines)
        graph.merge_node(
            CONTAINER_EVENT, event.key, event_props(event, why, key, until)
        )
    lookback = until - timedelta(hours=settings.container_sensor_max_lookback_hours)
    untold = untold_alarms(graph, lookback)
    cap = settings.container_sensor_max_lookback_hours if capped else None
    message_id, send_error = _tell(port, untold, settings=settings, capped_hours=cap)
    alarms = sum(1 for event in events if event.alarm)
    told = len(untold) if message_id is not None else 0
    props: dict[str, object] = {
        "read_from": start.isoformat(),
        "read_until": until.isoformat(),
        "outcome": READ_OK,
        "rows": len(rows),
        "recorded": len(events),
        "alarms": alarms,
        "reports": len(events) - alarms,
        "told": told,
        "capped": capped,
        "truncated": len(rows) >= EVENT_ROWS_MAX,
        "created_at": until.isoformat(),
    }
    if message_id is not None:
        props["message_id"] = message_id
    if send_error:
        props["send_error"] = send_error
    read = graph.merge_node(SENSOR_READ, key, props)
    if message_id is not None:
        for node in untold:
            graph.add_edge(read, node, TOLD)
    return SensorOutcome(key, len(rows), len(events), alarms, told, send_error)


def _new_events(graph: GraphStore, rows: Sequence[Row]) -> list[ContainerEvent]:
    found: dict[str, ContainerEvent] = {}
    for row in rows:
        event = classify(row)
        if event is None or event.key in found:
            continue
        if graph.get_node(CONTAINER_EVENT, event.key) is None:
            found[event.key] = event
    return list(found.values())


def _error_lines(
    reader: LogReader, events: Sequence[ContainerEvent], until: datetime
) -> _Lines:
    alarms = [event for event in events if event.alarm and event.replica]
    moments = [parse_instant(event.occurred_at) for event in alarms]
    known = [moment for moment in moments if moment is not None]
    if not known:
        return {}
    rows = reader.error_lines(
        [event.replica for event in alarms], min(known) - LINE_WINDOW, until
    )
    lines: _Lines = {}
    for row in rows:
        at = parse_instant(row.get("TimeGenerated"))
        if at is not None:
            replica = str(row.get("ContainerGroupName_s", ""))
            lines.setdefault(replica, []).append((at, str(row.get("Log_s", ""))))
    return lines


def _why(event: ContainerEvent, lines: _Lines) -> str:
    occurred = parse_instant(event.occurred_at)
    if not event.alarm or occurred is None:
        return ""
    return choose_line(lines.get(event.replica, []), occurred)


def _tell(
    port: AlarmPort,
    untold: Sequence[Node],
    *,
    settings: OrchestratorSettings,
    capped_hours: int | None,
) -> tuple[int | None, str]:
    if not untold:
        return None, ""
    text = alarm_message(
        group_events(node.props for node in untold),
        timezone=settings.operator_timezone,
        limit=settings.container_sensor_alarm_groups_max,
        capped_hours=capped_hours,
    )
    try:
        message_id = port.send_alarm(text=text)
    except Exception as exc:  # the port's text may quote the alarm: keep the type only
        return None, type(exc).__name__
    if message_id is None:
        error = str(getattr(port, "last_error", "") or "")
        return None, error if error.isidentifier() else "no message id"
    return message_id, ""
