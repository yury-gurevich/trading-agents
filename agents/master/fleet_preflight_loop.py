"""Schedule master fleet-preflight checks without terminating on one failure.

Agent: master
Role: repeat the fleet readiness check at a bounded interval.
External I/O: none directly (delegates to an injected readiness check and fault sink).
"""

from __future__ import annotations

from threading import Thread
from time import sleep
from typing import TYPE_CHECKING

from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from collections.abc import Callable

    from agents.master.fleet_preflight import FleetPreflightResult
    from kernel import FaultSink


def run_fleet_preflight_loop(
    run_once: Callable[[], FleetPreflightResult],
    *,
    sink: FaultSink,
    interval_minutes: int,
    sleep: Callable[[float], None],
    iterations: int | None = None,
) -> None:
    """Run preflight repeatedly; one crashing iteration faults but does not stop it."""
    completed = 0
    while iterations is None or completed < iterations:
        with fault_boundary(
            sink,
            agent="master",
            module="agents.master.fleet_preflight_loop",
            capability="fleet_preflight",
            reraise=False,
        ):
            run_once()
        completed += 1
        if iterations is None or completed < iterations:
            sleep(interval_minutes * 60.0)


def start_fleet_preflight_daemon(
    run_once: Callable[[], FleetPreflightResult],
    *,
    sink: FaultSink,
    interval_minutes: int,
) -> None:
    """Start the master-owned preflight schedule without blocking HTTP serving."""
    Thread(
        target=run_fleet_preflight_loop,
        kwargs={
            "run_once": run_once,
            "sink": sink,
            "interval_minutes": interval_minutes,
            "sleep": sleep,
        },
        name="fleet-preflight",
        daemon=True,
    ).start()
