"""Master fleet-check schedule stop proofs.

Agent: master
Role: prove no check starts after stop and a daemon's idle wait is interrupted.
External I/O: none.
"""

from __future__ import annotations

import threading

from agents.master.fleet_preflight import FleetPreflightResult
from agents.master.fleet_preflight_loop import (
    run_fleet_preflight_loop,
    start_fleet_preflight_daemon,
)
from kernel import CollectingFaultSink
from kernel.stop import StopSignal


def test_a27_schedule_runs_no_check_after_stop() -> None:
    """MST-ORD-04: a stop requested in a check ends the schedule after that check."""
    stop = StopSignal()
    calls: list[str] = []

    def check() -> FleetPreflightResult:
        calls.append("check")
        stop.request("SIGTERM")
        return FleetPreflightResult(True, ())

    run_fleet_preflight_loop(
        check,
        sink=CollectingFaultSink(),
        interval_minutes=60,
        sleep=stop.wait,
        should_stop=lambda: stop.requested,
        iterations=2,
    )
    assert calls == ["check"]


def test_a27_daemon_wakes_from_schedule_wait_on_stop() -> None:
    """MST-ORD-04: the returned daemon is alive before stop and ends promptly."""
    stop = StopSignal()
    checked = threading.Event()
    calls: list[str] = []

    def check() -> FleetPreflightResult:
        calls.append("check")
        checked.set()
        return FleetPreflightResult(True, ())

    thread = start_fleet_preflight_daemon(
        check,
        sink=CollectingFaultSink(),
        interval_minutes=60,
        stop=stop,
    )
    try:
        assert checked.wait(2)
        assert thread.is_alive()
        assert thread.daemon
        assert thread.name == "fleet-preflight"
    finally:
        stop.request("SIGTERM")
        thread.join(timeout=2)
    assert not thread.is_alive()
    assert calls == ["check"]
