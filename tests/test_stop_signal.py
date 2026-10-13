"""Stop flag and handler proofs for S272.

Agent: kernel
Role: prove first-request timing, real waits and safe signal installation.
External I/O: SIGTERM and descriptor 2; previous handlers are always restored.
"""

from __future__ import annotations

import signal
import threading
import time

import pytest

from kernel.stop import StopSignal, install


@pytest.fixture(autouse=True)
def _restore_sigterm():
    previous = signal.getsignal(signal.SIGTERM)
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, previous)


def test_a10_first_stop_keeps_its_reason_and_time() -> None:
    """MST-TRG-03 / MST-ORD-04: the drain budget starts at the first request."""
    clock = [100.0]
    stop = StopSignal(lambda: clock[0])
    assert not stop.requested
    assert stop.reason == ""
    assert stop.seconds_since_request() == 0.0
    assert stop.seconds_left(20) == 20
    stop.request("SIGTERM")
    clock[0] = 103.0
    stop.request("later")
    assert stop.requested
    assert stop.reason == "SIGTERM"
    assert stop.seconds_since_request() == 3.0
    assert stop.seconds_left(20) == 17
    clock[0] = 130.0
    assert stop.seconds_left(20) == 0.0


def test_a10_wait_uses_real_time_and_wakes_on_stop() -> None:
    """MST-TRG-03 / MST-ORD-04: a fake reporting clock cannot prolong wait()."""
    stop = StopSignal(lambda: 100.0)
    timer = threading.Timer(0.05, stop.request)
    started = time.monotonic()
    timer.start()
    try:
        stop.wait(30)
        assert time.monotonic() - started < 2.0
    finally:
        timer.cancel()
        timer.join(timeout=2)
    idle = StopSignal(lambda: 100.0)
    started = time.monotonic()
    idle.wait(0.03)
    assert 0.02 <= time.monotonic() - started < 1.0
    started = time.monotonic()
    idle.wait(-10)
    assert time.monotonic() - started < 0.1


def test_a11_handler_sets_the_flag_and_writes_exactly() -> None:
    """MST-TRG-03 / MST-OBS-05: SIGTERM sets the flag and names the agent."""
    stop = StopSignal()
    lines: list[str] = []
    assert install(stop, agent="scanner", write=lines.append)
    timer = threading.Timer(0.02, lambda: signal.raise_signal(signal.SIGTERM))
    started = time.monotonic()
    timer.start()
    try:
        stop.wait(2)
        assert time.monotonic() - started < 1.5
    finally:
        timer.cancel()
        timer.join(timeout=2)
    assert stop.requested
    assert stop.reason == "SIGTERM"
    assert lines == ["[scanner] stop signal SIGTERM: taking no new work\n"]


def test_a11_default_writer_uses_descriptor_two(capfd) -> None:
    """MST-TRG-03 / MST-OBS-05: the default signal line reaches raw stderr."""
    stop = StopSignal()
    assert install(stop, agent="monitor")
    timer = threading.Timer(0.02, lambda: signal.raise_signal(signal.SIGTERM))
    timer.start()
    try:
        stop.wait(2)
    finally:
        timer.cancel()
        timer.join(timeout=2)
    assert capfd.readouterr().err == (
        "[monitor] stop signal SIGTERM: taking no new work\n"
    )
    assert stop.requested
    assert stop.reason == "SIGTERM"


def test_a11_second_thread_installs_nothing() -> None:
    """MST-TRG-03 / MST-OBS-05: installing off the main thread is a quiet refusal."""
    previous = signal.getsignal(signal.SIGTERM)
    stop = StopSignal()
    answers: list[bool] = []
    thread = threading.Thread(
        target=lambda: answers.append(install(stop, agent="operator"))
    )
    thread.start()
    thread.join(timeout=2)
    assert not thread.is_alive()
    assert answers == [False]
    assert signal.getsignal(signal.SIGTERM) is previous
    assert not stop.requested
