"""Master's HTTP routes and the serve() wiring on a real socket (S244).

Agent: master
Role: prove the production handler's health, 404 and bad-JSON answers, and that
      serve() builds its server from MasterSettings (backlog, replay lifetime).
External I/O: a loopback TCP socket on an OS-assigned port (no other network).
"""

from __future__ import annotations

import pytest

from agents.master import http_server
from agents.master.activation_replay import ActivationReplay
from agents.master.http_server import EhloServer, build_server, serve
from agents.master.settings import MasterSettings
from agents.master.tests.ehlo_server_support import request, running, slow_master
from kernel.crypto import generate_keypair


@pytest.fixture(autouse=True)
def _loopback_bypasses_any_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("NO_PROXY", "no_proxy"):
        monkeypatch.setenv(name, "127.0.0.1,localhost")


def test_the_server_answers_health_and_refuses_the_rest() -> None:
    """Bad JSON is 400 with no write; unknown paths are 404; health is 200."""
    agent = slow_master(0.0)
    server = build_server(
        "127.0.0.1", 0, agent, "", replay=ActivationReplay(1.0), backlog=16
    )
    with running(server) as url:
        assert request(f"{url}/health", "GET") == (200, {"status": "ok"})
        assert request(f"{url}/metrics", "GET")[0] == 200
        assert request(f"{url}/nope", "GET") == (404, {"error": "not_found"})
        assert request(f"{url}/nope", "POST", b"{}") == (404, {"error": "not_found"})
        assert request(f"{url}/ehlo", "POST", b"not json") == (
            400,
            {"error": "bad_json"},
        )
    assert agent._graph.list_nodes("AgentInstance") == ()


def test_serve_builds_its_server_from_master_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MST-ORD-03 / MST-IDM-03: serve() uses the backlog tunable and replay lifetime."""
    served: list[EhloServer] = []

    def record(self: EhloServer) -> None:
        served.append(self)

    monkeypatch.setattr(http_server.EhloServer, "serve_forever", record)
    settings = MasterSettings(ehlo_listen_backlog=32, handshake_timeout_2_seconds=120)

    serve(0, slow_master(0.0), generate_keypair()[0], settings, host="127.0.0.1")

    (server,) = served
    assert server.request_queue_size == 32
    assert server.replay._lifetime == 120.0
    assert server.socket.fileno() == -1  # closed when serve() returned
