"""Graph-pull stop and bounded-pass compatibility proofs.

Agent: kernel
Role: prove no further item starts and cleanup happens only on a stop.
External I/O: captured stderr only.
"""

from __future__ import annotations

import signal

import pytest

from kernel import InMemoryGraphStore
from kernel.stop import StopSignal
from kernel.work_loop import run_once, work_loop


class ClosingGraph(InMemoryGraphStore):
    closes = 0

    def close(self):
        self.closes += 1


def test_a4_a_pass_starts_no_item_after_stop() -> None:
    """MST-TRG-03: finish item two and leave item three pending."""
    pending = ["one", "two", "three"]
    processed: list[str] = []
    stop = StopSignal()

    def process(item):
        processed.append(item)
        pending.remove(item)
        if item == "two":
            stop.request("SIGTERM")

    result = run_once(
        lambda: list(pending), process, should_stop=lambda: stop.requested
    )
    assert processed == ["one", "two"]
    assert pending == ["three"]
    assert (result.found, result.attempted, result.advanced) == (3, 2, 2)


def test_a5_stopped_loop_flushes_closes_without_sleep(capsys) -> None:
    """MST-TRG-03 / MST-OBS-05: one stopped pass cleans up and says so exactly."""
    graph = ClosingGraph()
    stop = StopSignal(lambda: 10.0)
    pending = ["one", "two"]
    sleeps: list[float] = []
    flushes: list[str] = []

    def process(item):
        pending.remove(item)
        stop.request("SIGTERM")

    results = work_loop(
        lambda: list(pending),
        process,
        graph=graph,
        agent="execution",
        stop=stop,
        sleep=sleeps.append,
        flush_faults=lambda: flushes.append("faults"),
        max_iterations=2,
    )
    assert len(results) == 1
    assert pending == ["two"]
    assert sleeps == []
    assert flushes == ["faults"]
    assert graph.closes == 1
    assert capsys.readouterr().err == (
        "[execution] stopped on SIGTERM after 0.0 s: closed faults, graph; exit 0\n"
    )


def test_a6_pass_limit_installs_nothing_and_closes_nothing(capsys) -> None:
    """MST-TRG-03: a bounded loop keeps its existing final flush and quiet return."""
    graph = ClosingGraph()
    flushes: list[str] = []
    previous = signal.getsignal(signal.SIGTERM)
    results = work_loop(
        list,
        lambda item: None,
        graph=graph,
        max_iterations=2,
        poll_interval=0.001,
        flush_faults=lambda: flushes.append("faults"),
    )
    assert len(results) == 2
    assert graph.closes == 0
    assert flushes == ["faults"]
    assert capsys.readouterr().err == ""
    assert signal.getsignal(signal.SIGTERM) is previous


def test_a7_graph_close_failure_exits_one_without_error_text(capsys) -> None:
    """MST-TRG-03 / MST-OBS-05: a close failure is exit 1 with type alone."""

    class RefusingGraph(ClosingGraph):
        def close(self):
            self.closes += 1
            raise ConnectionError("private-marker")

    graph = RefusingGraph()
    stop = StopSignal(lambda: 10.0)
    stop.request("SIGTERM")
    with pytest.raises(SystemExit) as caught:
        work_loop(list, lambda item: None, graph=graph, stop=stop)
    assert caught.value.code == 1
    assert graph.closes == 1
    line = capsys.readouterr().err
    assert line == (
        "[agent] stopped on SIGTERM after 0.0 s: "
        "NOT closed graph (ConnectionError); exit 1\n"
    )
    assert "private-marker" not in line
