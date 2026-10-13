"""Master's shared signal-relative drain deadline proofs.

Agent: master
Role: prove the server and fleet check receive only the unspent signal budget.
External I/O: none; synthetic socket and thread boundaries.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from agents.master import http_server
from agents.master.agent import MasterAgent
from agents.master.settings import MasterSettings
from agents.master.stopping import shut_down
from kernel import InMemoryGraphStore
from kernel.stop import StopSignal

if TYPE_CHECKING:
    from threading import Thread

    import pytest


def _elapsed_stop() -> StopSignal:
    clock = [10.0]
    stop = StopSignal(lambda: clock[0])
    stop.request("SIGTERM")
    clock[0] = 17.0
    return stop


def test_server_drain_budget_counts_from_the_signal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MST-ORD-04: close the socket before draining only the 13 unspent seconds."""
    events: list[object] = []

    class Server:
        def server_close(self) -> None:
            events.append("socket")

        def drain(self, seconds: float) -> int:
            events.append(seconds)
            return 2

    monkeypatch.setattr(http_server, "build_server", lambda *_a, **_k: Server())
    assert (
        http_server.serve(
            0,
            MasterAgent(InMemoryGraphStore()),
            "",
            MasterSettings(),
            stop=_elapsed_stop(),
        )
        == 2
    )
    assert events == ["socket", 13.0]


def test_fleet_check_uses_the_same_remaining_budget() -> None:
    """MST-ORD-04: the check receives the same signal deadline, never a new budget."""
    waits: list[float | None] = []

    class Check:
        def join(self, seconds: float | None = None) -> None:
            waits.append(seconds)

        def is_alive(self) -> bool:
            return False

    graph = InMemoryGraphStore()
    agent = MasterAgent(graph)
    agent.start()
    assert (
        shut_down(
            agent,
            graph,
            _elapsed_stop(),
            activations_left=0,
            preflight=cast("Thread", Check()),
            settings=MasterSettings(),
            write=lambda _line: None,
        )
        == 0
    )
    assert waits == [13.0]
