"""The daily brief's container line: what the sensor recorded in the last day.

Agent: orchestration
Role: say in one line whether the sensor read, and which alarms it recorded (DL-301).
External I/O: reads the injected GraphStore.

No line before the sensor's first read, so a fleet that has never run it briefs as
before. After that the line is always there: a sensor that stopped reading says so.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from orchestration.container_alarm_text import brief_summary, group_events
from orchestration.container_sensor_graph import CONTAINER_EVENT, READ_OK, SENSOR_READ
from orchestration.daily_brief_fills import parse_instant
from orchestration.daily_brief_text import local_stamp

if TYPE_CHECKING:
    from datetime import datetime

    from kernel import GraphStore

BRIEF_WINDOW = timedelta(hours=24)


def container_line(graph: GraphStore, *, now: datetime, timezone: str) -> str | None:
    """Return the brief's container line, or None before the sensor's first read."""
    reads = [
        (moment, node)
        for node in graph.list_nodes(SENSOR_READ)
        if (moment := parse_instant(node.props.get("read_until"))) is not None
    ]
    if not reads:
        return None
    latest_at, latest = max(reads, key=lambda item: (item[0], item[1].key))
    stamp = local_stamp(latest_at, timezone)
    if latest.props.get("outcome") != READ_OK:
        error = latest.props.get("error", "")
        return f"Containers: the sensor's last read failed ({error}) at {stamp}"
    since = now - BRIEF_WINDOW
    if latest_at < since:
        return f"Containers: the sensor has not read since {stamp}"
    recorded = [
        node.props
        for node in graph.list_nodes(CONTAINER_EVENT)
        if node.props.get("alarm") is True
        and (created := parse_instant(node.props.get("created_at"))) is not None
        and created >= since
    ]
    if not recorded:
        return "Containers: no alarm in 24 hours"
    groups = group_events(recorded)
    total = sum(group.times for group in groups)
    noun = "alarm" if total == 1 else "alarms"
    return f"Containers: {total} {noun} in 24 hours: {brief_summary(groups)}"
