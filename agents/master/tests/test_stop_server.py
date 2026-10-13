"""Master stop and in-flight activation proofs.

Agent: master
Role: exercise the production accept/drain loop on real loopback sockets.
External I/O: loopback HTTP and SIGTERM; previous handlers are restored.
"""

from __future__ import annotations

import json
import signal
import socketserver
import threading
from typing import TYPE_CHECKING, Any

import pytest

from agents.master import http_server
from agents.master.http_server import EhloServer, serve
from agents.master.settings import MasterSettings
from agents.master.tests.ehlo_server_support import request, slow_master
from kernel.crypto import generate_keypair
from kernel.stop import StopSignal

if TYPE_CHECKING:
    from collections.abc import Iterator

    from agents.master.agent import MasterAgent
    from kernel.handshake import ACTIVATEMessage, EHLOMessage

type Capture = tuple[list[EhloServer], threading.Event]


@pytest.fixture(autouse=True)
def _restore_handler_and_proxy(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    previous = signal.getsignal(signal.SIGTERM)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, previous)


@pytest.fixture
def capture(monkeypatch: pytest.MonkeyPatch) -> Capture:
    servers: list[EhloServer] = []
    ready = threading.Event()
    build = http_server.build_server

    def record(*args: Any, **kwargs: Any) -> EhloServer:
        server = build(*args, **kwargs)
        servers.append(server)
        ready.set()
        return server

    monkeypatch.setattr(http_server, "build_server", record)
    return servers, ready


def _run(
    capture: Capture, agent: MasterAgent, stop: StopSignal, budget: float = 20.0
) -> tuple[threading.Thread, list[int], str]:
    results: list[int] = []
    key = generate_keypair()[0]
    thread = threading.Thread(
        target=lambda: results.append(
            serve(
                0,
                agent,
                key,
                MasterSettings(stop_drain_seconds=budget),
                host="127.0.0.1",
                stop=stop,
            )
        ),
        daemon=True,
    )
    thread.start()
    assert capture[1].wait(5)
    server = capture[0][0]
    return thread, results, f"http://127.0.0.1:{server.server_address[1]}"


def test_a16_server_answers_health_then_stops(capture: Capture) -> None:
    """MST-ORD-04: stop returns zero and closes the listening socket."""
    stop = StopSignal()
    thread, results, url = _run(capture, slow_master(0), stop)
    try:
        assert request(url + "/health", "GET") == (200, {"status": "ok"})
    finally:
        stop.request("SIGTERM")
        thread.join(timeout=5)
    assert not thread.is_alive()
    assert results == [0]
    assert capture[0][0].socket.fileno() == -1


def _activation_at_stop(
    capture: Capture, monkeypatch: pytest.MonkeyPatch, delay: float, budget: float
) -> tuple[int, MasterAgent, list[int]]:
    stop = StopSignal()
    agent = slow_master(delay)
    activate = agent.activate
    timer = threading.Timer(0.2, lambda: stop.request("SIGTERM"))

    def stopping_activation(ehlo: EHLOMessage) -> ACTIVATEMessage:
        timer.start()
        return activate(ehlo)

    monkeypatch.setattr(agent, "activate", stopping_activation)
    thread, results, url = _run(capture, agent, stop, budget)
    body = json.dumps(
        {
            "ephemeral_boot_id": "s272",
            "agent_type": "scanner",
            "capability_declaration": {},
        }
    ).encode()
    try:
        status, _answer = request(url + "/ehlo", "POST", body)
    finally:
        stop.request("SIGTERM")
        timer.cancel()
        timer.join(timeout=2)
        thread.join(timeout=5)
    assert not thread.is_alive()
    assert capture[0][0].socket.fileno() == -1
    return status, agent, results


def test_a17_activation_in_hand_is_answered(
    capture: Capture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """MST-ORD-04: a half-second activation finishes after stop and is answered."""
    status, agent, results = _activation_at_stop(capture, monkeypatch, 0.5, 20)
    assert status == 200
    assert results == [0]
    assert len(agent._graph.list_nodes("AgentInstance")) == 1


def test_a18_activation_outlasting_the_drain_is_reported(
    capture: Capture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """MST-ORD-04: a one-second activation with zero drain is counted unfinished."""
    status, _agent, results = _activation_at_stop(capture, monkeypatch, 1.0, 0)
    assert status == 200
    assert results == [1]


def test_a19_server_installs_its_own_sigterm_handler(
    capfd: pytest.CaptureFixture[str],
) -> None:
    """MST-TRG-03 / MST-ORD-04: the main-thread server listens without a stop arg."""
    timer = threading.Timer(0.2, lambda: signal.raise_signal(signal.SIGTERM))
    timer.start()
    try:
        left = serve(0, slow_master(0), "", MasterSettings(), host="127.0.0.1")
    finally:
        timer.cancel()
        timer.join(timeout=2)
    assert left == 0
    assert (
        capfd.readouterr().err == "[master] stop signal SIGTERM: taking no new work\n"
    )


def test_a20_failed_request_thread_is_counted_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MST-ORD-04: a thread-start failure propagates and leaves no drain work."""

    def refuse(_self: threading.Thread) -> None:
        raise RuntimeError("thread-start-marker")

    server = EhloServer(("127.0.0.1", 0), socketserver.BaseRequestHandler)
    monkeypatch.setattr(threading.Thread, "start", refuse)
    try:
        with pytest.raises(RuntimeError, match="thread-start-marker"):
            server.process_request(object(), ("127.0.0.1", 0))
        assert server.drain(0) == 0
    finally:
        server.server_close()
