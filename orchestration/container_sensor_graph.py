"""The container sensor's graph facts: its reads, its events and what was told.

Agent: orchestration
Role: name the sensor's labels and keys, find where the last read ended, and find the
    alarms no read has told yet (DL-301).
External I/O: reads the injected GraphStore.
"""

from __future__ import annotations

from datetime import UTC, timedelta
from typing import TYPE_CHECKING

from orchestration.daily_brief_fills import parse_instant

if TYPE_CHECKING:
    from datetime import datetime

    from kernel import GraphStore, Node
    from orchestration.container_events import ContainerEvent
    from orchestration.settings import OrchestratorSettings

CONTAINER_EVENT = "ContainerEvent"
SENSOR_READ = "ContainerSensorRead"
TOLD = "TOLD"  # ContainerSensorRead -> ContainerEvent: the read whose message told it
READ_OK = "read"
READ_FAILED = "failed"


def read_key(until: datetime) -> str:
    """Name the read that ends at ``until``."""
    return f"container-sensor-read:{until.astimezone(UTC).isoformat()}"


def read_window(
    previous: datetime | None, until: datetime, settings: OrchestratorSettings
) -> tuple[datetime, bool]:
    """Return where this read starts, and whether the look-back cap cut it."""
    if previous is None:
        start = until - timedelta(hours=settings.container_sensor_first_read_hours)
    else:
        start = previous - timedelta(minutes=settings.container_sensor_overlap_minutes)
    floor = until - timedelta(hours=settings.container_sensor_max_lookback_hours)
    return (floor, True) if start < floor else (start, False)


def last_read_until(graph: GraphStore) -> datetime | None:
    """Return where the latest successful read ended, or None before the first."""
    ends = [
        parse_instant(node.props.get("read_until"))
        for node in graph.list_nodes(SENSOR_READ)
        if node.props.get("outcome") == READ_OK
    ]
    return max((end for end in ends if end is not None), default=None)


def untold_alarms(graph: GraphStore, since: datetime) -> list[Node]:
    """Return the alarm events recorded since ``since`` that no read has told."""
    keys = graph.keys_without_edge(
        CONTAINER_EVENT, TOLD, downstream=False, created_at_from=since
    )
    nodes = (graph.get_node(CONTAINER_EVENT, key) for key in keys)
    alarms = [
        node for node in nodes if node is not None and node.props.get("alarm") is True
    ]
    return sorted(
        alarms, key=lambda node: (str(node.props.get("occurred_at", "")), node.key)
    )


def event_props(
    event: ContainerEvent, why: str, key: str, until: datetime
) -> dict[str, object]:
    """Return the properties one recorded event holds."""
    props: dict[str, object] = {
        "app": event.app,
        "revision": event.revision,
        "replica": event.replica,
        "kind": event.kind,
        "alarm": event.alarm,
        "reason": event.reason,
        "message": event.message,
        "times": event.times,
        "occurred_at": event.occurred_at,
        "error_line": why,
        "read_key": key,
        "created_at": until.isoformat(),
    }
    if event.exit_code is not None:
        props["exit_code"] = event.exit_code
    return props
