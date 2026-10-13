"""Schedule master fleet-preflight checks without terminating on one failure.

Agent: master
Role: repeat the fleet readiness check at a bounded interval, until told to stop.
External I/O: none directly (delegates to an injected readiness check and fault sink).
"""

from __future__ import annotations

from threading import Thread
from typing import TYPE_CHECKING

from kernel.errors import fault_boundary
from kernel.stop import StopSignal

if TYPE_CHECKING:
    from collections.abc import Callable

    from agents.master.fleet_preflight import FleetPreflightResult
    from kernel import FaultSink


def _never() -> bool:
    return False


def run_fleet_preflight_loop(
    run_once: Callable[[], FleetPreflightResult],
    *,
    sink: FaultSink,
    interval_minutes: int,
    sleep: Callable[[float], None],
    iterations: int | None = None,
    should_stop: Callable[[], bool] = _never,
) -> None:
    """Run preflight repeatedly; one crashing iteration faults but does not stop it.

    Once *should_stop* answers yes no further check starts.
    """
    completed = 0
    while not should_stop() and (iterations is None or completed < iterations):
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
    stop: StopSignal | None = None,
) -> Thread:
    """Start the master-owned preflight schedule without blocking HTTP serving.

    The schedule sleeps on *stop*, so a stop ends the wait between two checks at
    once; the thread is returned so the stop can wait for a check in hand.
    """
    stopping = stop if stop is not None else StopSignal()
    thread = Thread(
        target=run_fleet_preflight_loop,
        kwargs={
            "run_once": run_once,
            "sink": sink,
            "interval_minutes": interval_minutes,
            "sleep": stopping.wait,
            "should_stop": lambda: stopping.requested,
        },
        name="fleet-preflight",
        daemon=True,
    )
    thread.start()
    return thread
