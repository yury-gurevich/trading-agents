"""The fault boundary around the container sensor, and its wiring from the job's env.

Agent: orchestration
Role: run the sensor on every dispatcher fire so that no failure of it reaches the fire.
External I/O: process environment; builds the graph and the Telegram port through
    injected factories; writes Fault and ContainerSensorRead nodes; returns one line.

The script imports this module and nothing else of the sensor. The sensor itself is
imported inside the `try` below, so a module the image lacks is a fault and the fire
is unchanged (`DSP-FAIL-04`). A line or a fault names a step, an error type and a
status word, never a value (`DSP-SEC-03`).
"""

from __future__ import annotations

import os
import sys
from datetime import UTC
from typing import TYPE_CHECKING, cast

from kernel import CollectingFaultSink, GraphFaultSink
from kernel.errors import fault_boundary
from orchestration.settings import OrchestratorSettings

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from datetime import datetime

    from kernel import GraphStore
    from orchestration.container_logs import LogReader
    from orchestration.container_sensor import AlarmPort, SensorOutcome

WORKSPACE_ENV = "LOG_ANALYTICS_WORKSPACE_ID"


class ContainerSensorFailedError(RuntimeError):
    """The sensor did not read or did not tell; names the step and error type only."""


def sense_from_env(
    *,
    now: datetime,
    graph_factory: Callable[[], object],
    port_factory: Callable[[], object],
    environ: Mapping[str, str] | None = None,
) -> str | None:
    """Run the sensor when the job is configured for it; return the line to print."""
    env = os.environ if environ is None else environ
    workspace = env.get(WORKSPACE_ENV, "").strip()
    if not workspace:
        return None  # not configured: the fire's own output stays as it was
    if not env.get("POSTGRES_DSN"):
        return "error container-sensor not run: POSTGRES_DSN is required"
    try:
        from orchestration.container_logs import LogAnalyticsReader

        settings = OrchestratorSettings()
        reader = LogAnalyticsReader(
            workspace,
            environ=dict(env),
            timeout=settings.container_sensor_timeout_seconds,
        )
        graph = cast("GraphStore", graph_factory())
    except Exception as exc:  # the boundary itself: a type name, never a message
        return f"error container-sensor not run: {type(exc).__name__}"
    try:
        port = cast("AlarmPort", port_factory())
        return sense_safely(graph, reader, port, now=now, settings=settings)
    finally:
        close = getattr(graph, "close", None)
        if callable(close):
            try:
                close()
            except Exception as exc:  # a close that fails must not end the fire
                sys.stderr.write(
                    f"error container-sensor close: {type(exc).__name__}\n"
                )


def sense_safely(
    graph: GraphStore,
    reader: LogReader,
    port: AlarmPort,
    *,
    now: datetime,
    settings: OrchestratorSettings,
) -> str:
    """Run one read; any failure becomes one Fault and a failed read, never a raise."""
    try:
        from orchestration.container_sensor import sense_containers

        outcome = sense_containers(graph, reader, port, now=now, settings=settings)
    except Exception as exc:  # the boundary itself: a type and a status word
        failure = _failure(exc)
    else:
        return _told(graph, outcome)
    # Recorded once the handler has ended, so the Fault's traceback chains no earlier
    # error and the exception's own text never reaches the graph (DSP-SEC-03).
    _record_failed_read(graph, now, failure)
    _record(graph, f"container sensor did not read: {failure}")
    return f"error container-sensor failed: {failure}"


def _told(graph: GraphStore, outcome: SensorOutcome) -> str:
    line = (
        f"container-sensor read {outcome.rows} rows: {outcome.recorded} new events, "
        f"{outcome.alarms} alarms, told {outcome.told}"
    )
    if outcome.send_error:
        _record(graph, f"container alarm not sent: {outcome.send_error}")
        line += f", send failed ({outcome.send_error})"
    return line


def _failure(exc: Exception) -> str:
    status = getattr(exc, "status", "")
    name = type(exc).__name__
    return f"{name} ({status})" if isinstance(status, str) and status else name


def _record_failed_read(graph: GraphStore, now: datetime, failure: str) -> None:
    try:
        from orchestration.container_sensor_graph import (
            READ_FAILED,
            SENSOR_READ,
            read_key,
        )

        until = now.astimezone(UTC).isoformat()
        graph.merge_node(
            SENSOR_READ,
            read_key(now),
            {
                "read_until": until,
                "outcome": READ_FAILED,
                "error": failure,
                "created_at": until,
            },
        )
    except Exception as exc:  # the graph refused it: the Fault below still tries
        sys.stderr.write(
            f"error container-sensor read not recorded: {type(exc).__name__}\n"
        )


def _record(graph: GraphStore, message: str) -> None:
    # Raised outside any `except`, so the Fault's traceback chains no earlier error.
    try:
        with fault_boundary(
            GraphFaultSink(graph, CollectingFaultSink()),
            agent="orchestration",
            module="orchestration.container_sensor",
            capability="container_sensor",
            reraise=False,
        ):
            raise ContainerSensorFailedError(message)
    except Exception as exc:  # the graph refused the fault itself
        sys.stderr.write(
            f"error container-sensor fault not recorded: {type(exc).__name__}\n"
        )
