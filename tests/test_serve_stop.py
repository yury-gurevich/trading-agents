"""Served-agent stop proofs.

Agent: kernel
Role: prove idle interruption and completion of requests already taken.
External I/O: SIGTERM and captured stderr; the previous handler is restored.
"""

from __future__ import annotations

import signal
import threading

import pytest

from kernel import CollectingFaultSink, InMemoryGraphStore, InProcessBus
from kernel.envelope import AgentMessage
from kernel.serve_loop import LocalRequestConsumer, serve_loop
from kernel.stop import StopSignal


@pytest.fixture(autouse=True)
def _restore_sigterm():
    previous = signal.getsignal(signal.SIGTERM)
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, previous)


def test_a3_idle_serve_loop_listens_for_sigterm(capfd) -> None:
    """MST-TRG-03: an empty served inbox wakes and returns zero on SIGTERM."""
    timer = threading.Timer(0.2, lambda: signal.raise_signal(signal.SIGTERM))
    timer.start()
    try:
        count = serve_loop(LocalRequestConsumer(), InProcessBus(), agent="operator")
    finally:
        timer.cancel()
        timer.join(timeout=2)
    assert count == 0
    lines = capfd.readouterr().err.splitlines()
    assert len(lines) == 2
    assert lines[0] == "[operator] stop signal SIGTERM: taking no new work"
    assert lines[-1].startswith("[operator] stopped on SIGTERM after ")
    assert lines[-1].endswith("nothing to close; exit 0")


class ClosingInbox(LocalRequestConsumer):
    def __init__(self, stop, *, stop_on=1):
        super().__init__()
        self.stop = stop
        self.stop_on = stop_on
        self.polls = 0
        self.closes = 0

    def poll(self):
        self.polls += 1
        if self.polls == self.stop_on:
            self.stop.request("SIGTERM")
            return super().poll()
        return []

    def close(self):
        self.closes += 1


class ClosingGraph(InMemoryGraphStore):
    closes = 0

    def close(self):
        self.closes += 1


class FlushingSink(CollectingFaultSink):
    flushes = 0

    def flush(self):
        self.flushes += 1


def _answered_inbox(stop, stop_on=1):
    inbox = ClosingInbox(stop, stop_on=stop_on)
    inbox.submit(
        AgentMessage(
            sender="caller",
            recipient="operator",
            message_type="request",
            capability="echo",
            payload={"n": 2},
        )
    )
    bus = InProcessBus()
    bus.register("operator", "echo", lambda p: {"answer": p["n"] * 2})
    return inbox, bus


def test_a8_taken_request_is_answered_before_closure(capsys) -> None:
    """MST-TRG-03: the request taken at stop is answered once, then all is closed."""
    stop = StopSignal(lambda: 10.0)
    inbox, bus = _answered_inbox(stop)
    graph = ClosingGraph()
    sink = FlushingSink()
    assert serve_loop(inbox, bus, graph=graph, sink=sink, stop=stop) == 1
    assert inbox.polls == inbox.closes == graph.closes == sink.flushes == 1
    assert len(inbox.replies) == 1
    assert inbox.replies[0].message_type == "response"
    assert inbox.replies[0].payload == {"answer": 4}
    assert capsys.readouterr().err == (
        "[agent] stopped on SIGTERM after 0.0 s: "
        "closed faults, requests, graph; exit 0\n"
    )


def test_a9_idle_loop_polls_again_until_the_stop(capsys) -> None:
    """MST-TRG-03: zero idle sleep still polls until the third poll takes work."""
    stop = StopSignal(lambda: 10.0)
    inbox, bus = _answered_inbox(stop, stop_on=3)
    assert serve_loop(inbox, bus, stop=stop, poll_interval=0) == 1
    assert inbox.polls == 3
    assert inbox.closes == 1
    assert len(inbox.replies) == 1
    assert capsys.readouterr().err.endswith("closed requests; exit 0\n")
