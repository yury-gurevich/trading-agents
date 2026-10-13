"""Master session-end and failed-shutdown proofs.

Agent: master
Role: prove session evidence survives unfinished work and failed end writes.
External I/O: none; an in-memory graph and synthetic fleet-check threads.
"""

from __future__ import annotations

import threading
from datetime import datetime
from typing import TYPE_CHECKING

import pytest

from agents.master.agent import MasterAgent
from agents.master.settings import MasterSettings
from agents.master.stopping import end_session, shut_down
from agents.master.store import write_session
from kernel import InMemoryGraphStore
from kernel.stop import StopSignal

if TYPE_CHECKING:
    from kernel.graph import Node
    from kernel.graph_support import Props


class ClosingGraph(InMemoryGraphStore):
    def __init__(self) -> None:
        super().__init__()
        self.closes = 0
        self.order: list[str] = []

    def close(self) -> None:
        self.closes += 1
        self.order.append("graph")


def _finished() -> threading.Thread:
    thread = threading.Thread(target=lambda: None)
    thread.start()
    thread.join(timeout=2)
    assert not thread.is_alive()
    return thread


def _stop() -> StopSignal:
    stop = StopSignal(lambda: 10.0)
    stop.request("SIGTERM")
    return stop


def test_a21_session_starts_with_start_time_alone() -> None:
    """MST-OUT-03: no empty reason blocks the later append-only session end."""
    node = write_session(InMemoryGraphStore(), "session:test")
    assert set(node.props) == {"started_at"}
    assert datetime.fromisoformat(node.props["started_at"]).tzinfo is not None


def test_a22_stopped_master_ends_session_then_closes_graph(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MST-OUT-03 / MST-ORD-04 / MST-OBS-05: clean shutdown records its end once."""
    graph = ClosingGraph()
    agent = MasterAgent(graph)
    session_id = agent.start()
    start = graph.get_node("Session", session_id)
    assert start is not None
    started_at = datetime.fromisoformat(start.props["started_at"])
    merge = graph.merge_node

    def record(label: str, key: str, props: Props, *, schema_version: int = 1) -> Node:
        graph.order.append("session")
        return merge(label, key, props, schema_version=schema_version)

    monkeypatch.setattr(graph, "merge_node", record)
    lines: list[str] = []
    code = shut_down(
        agent,
        graph,
        _stop(),
        activations_left=0,
        preflight=_finished(),
        settings=MasterSettings(),
        write=lines.append,
    )
    node = graph.get_node("Session", session_id)
    assert node is not None
    assert datetime.fromisoformat(node.props["ended_at"]) > started_at
    assert node.props["shutdown_reason"] == "SIGTERM"
    assert set(node.props) == {"started_at", "ended_at", "shutdown_reason"}
    assert graph.closes == 1
    assert graph.order == ["session", "graph"]
    assert code == 0
    assert lines == [
        "[master] stopped on SIGTERM after 0.0 s: closed session, graph; exit 0\n"
    ]


def test_a23_work_left_is_named_and_session_still_ends() -> None:
    """MST-ORD-04 / MST-OUT-03: unfinished work is exit 1, with session end saved."""
    graph = ClosingGraph()
    agent = MasterAgent(graph)
    session_id = agent.start()
    release = threading.Event()
    thread = threading.Thread(target=release.wait, daemon=True)
    thread.start()
    lines: list[str] = []
    try:
        code = shut_down(
            agent,
            graph,
            _stop(),
            activations_left=2,
            preflight=thread,
            settings=MasterSettings(stop_drain_seconds=0),
            write=lines.append,
        )
    finally:
        release.set()
        thread.join(timeout=2)
    node = graph.get_node("Session", session_id)
    assert node is not None
    assert "ended_at" in node.props
    assert graph.closes == 1
    assert code == 1
    assert lines == [
        "[master] stopped on SIGTERM after 0.0 s: "
        "left 2 activation(s), the fleet check; closed session, graph; exit 1\n"
    ]


def test_a24_failed_session_write_still_closes_graph(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MST-ORD-04 / MST-OBS-05: a failed end write is named without its text."""
    graph = ClosingGraph()
    agent = MasterAgent(graph)
    agent.start()

    def refuse(*_args: object, **_kwargs: object) -> Node:
        raise ConnectionError("private-marker")

    monkeypatch.setattr(graph, "merge_node", refuse)
    lines: list[str] = []
    code = shut_down(
        agent,
        graph,
        _stop(),
        activations_left=0,
        preflight=_finished(),
        settings=MasterSettings(),
        write=lines.append,
    )
    assert code == 1
    assert graph.closes == 1
    assert lines == [
        "[master] stopped on SIGTERM after 0.0 s: "
        "closed graph; NOT closed session (ConnectionError); exit 1\n"
    ]
    assert "private-marker" not in lines[0]


def test_a25_master_without_start_ends_no_session() -> None:
    """MST-OUT-03: a master that opened no session has nothing to end."""
    graph = InMemoryGraphStore()
    lines: list[str] = []
    assert (
        shut_down(
            MasterAgent(graph),
            graph,
            _stop(),
            activations_left=0,
            preflight=_finished(),
            settings=MasterSettings(),
            write=lines.append,
        )
        == 0
    )
    assert graph.list_nodes("Session") == ()
    assert lines == [
        "[master] stopped on SIGTERM after 0.0 s: nothing to close; exit 0\n"
    ]


def test_a26_session_end_cannot_be_overwritten() -> None:
    """MST-OUT-03: a different second shutdown reason cannot replace the first."""
    graph = InMemoryGraphStore()
    write_session(graph, "session:test")
    end_session(graph, "session:test", reason="SIGTERM")
    with pytest.raises(ValueError, match="cannot be overwritten"):
        end_session(graph, "session:test", reason="different")
