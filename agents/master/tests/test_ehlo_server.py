"""Master serves an activation wave in parallel on a real socket (S244, DL-249 D4).

Agent: master
Role: run the production server on 127.0.0.1 port 0 and drive it with the real
      kernel EHLO client, so the concurrency clause is proven end to end.
External I/O: a loopback TCP socket on an OS-assigned port (no other network).
"""

from __future__ import annotations

import threading
import time

import pytest

from agents.master.activation_replay import ActivationReplay
from agents.master.http_server import EhloServer, build_server
from agents.master.tests.ehlo_server_support import (
    ACTIVATION_SECONDS,
    running,
    slow_master,
)
from agents.master.tests.helpers import trading_policy
from kernel.bootstrap import activate_agent
from kernel.crypto import generate_keypair


@pytest.fixture(autouse=True)
def _loopback_bypasses_any_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("NO_PROXY", "no_proxy"):
        monkeypatch.setenv(name, "127.0.0.1,localhost")


def test_an_activation_wave_is_served_in_parallel() -> None:
    """MST-ORD-03 / MST-TRG-01: 15 agents waking together all activate, concurrently.

    C8 — each activation takes ~0.5 s; served one at a time the wave would take
    over 7.5 s, served concurrently about one activation plus the RSA work
    (measured 1.37-1.46 s here); the bound is half the serial floor.
    """
    private, public = generate_keypair()
    agent = slow_master()
    server = build_server(
        "127.0.0.1", 0, agent, private, replay=ActivationReplay(300.0), backlog=64
    )
    agent_types = list(trading_policy())
    answers: dict[str, dict[str, object]] = {}
    errors: list[BaseException] = []
    start = threading.Barrier(len(agent_types))

    def boot(url: str, agent_type: str) -> None:
        start.wait()
        try:
            answers[agent_type] = activate_agent(url, agent_type, public_key_pem=public)
        except BaseException as exc:  # recorded and asserted below
            errors.append(exc)

    with running(server) as url:
        threads = [threading.Thread(target=boot, args=(url, t)) for t in agent_types]
        began = time.monotonic()
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=60)
        wall = time.monotonic() - began
    print(f"C8 wave: {len(agent_types)} activations in {wall:.2f}s")

    assert errors == []
    assert len(answers) == len(agent_types) == 15
    assert len({a["instance_id"] for a in answers.values()}) == 15
    assert len(agent._graph.list_nodes("AgentInstance")) == 15
    assert wall < len(agent_types) * ACTIVATION_SECONDS / 2


def test_the_listen_backlog_is_the_tunable() -> None:
    """MST-ORD-03: the server listens with the configured backlog, not Python's 5."""
    server = build_server(
        "127.0.0.1",
        0,
        slow_master(),
        generate_keypair()[0],
        replay=ActivationReplay(1.0),
        backlog=48,
    )
    try:
        assert server.request_queue_size == 48
        assert server.daemon_threads is True
    finally:
        server.server_close()


def test_a_server_that_cannot_bind_releases_its_socket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed bind closes the half-built server and raises (no leaked socket)."""
    closed: list[EhloServer] = []
    close = EhloServer.server_close

    def refuse_bind(_self: EhloServer) -> None:
        raise OSError("bind refused")

    def record_close(self: EhloServer) -> None:
        closed.append(self)
        close(self)

    monkeypatch.setattr(EhloServer, "server_bind", refuse_bind)
    monkeypatch.setattr(EhloServer, "server_close", record_close)

    with pytest.raises(OSError, match="bind refused"):
        build_server(
            "127.0.0.1", 0, slow_master(), "", replay=ActivationReplay(1.0), backlog=16
        )

    (server,) = closed
    assert server.socket.fileno() == -1
