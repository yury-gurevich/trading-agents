"""Master HTTP server — EHLO endpoint and health check.

Agent: master
Role: expose /ehlo (ACTIVATE handshake, a resent boot id replayed) and /health over
      HTTP on a threading server whose listen backlog holds an activation wave;
      run as the container's main blocking loop.
External I/O: TCP port 8000 (inbound HTTP).
"""

from __future__ import annotations

import http.server
import json
import socketserver
from typing import TYPE_CHECKING

from agents.master.activation_replay import ActivationReplay, replay_lifetime_seconds
from kernel.crypto import sign_pss
from kernel.handshake import EHLOMessage

if TYPE_CHECKING:
    from agents.master.agent import MasterAgent
    from agents.master.settings import MasterSettings


def handle_health() -> tuple[int, dict[str, object]]:
    """Return 200 OK with a status body."""
    return 200, {"status": "ok"}


def handle_ehlo(
    body: dict[str, object],
    agent: MasterAgent,
    private_key_pem: str,
    replay: ActivationReplay | None = None,
) -> tuple[int, dict[str, object]]:
    """Parse EHLO, activate (or replay the boot id's answer), return signed ACTIVATE.

    With *replay*, a repeated boot id of the same type gets the first signed answer
    and writes nothing; another type on that boot id is a 422 (MST-IDM-03).
    """
    try:
        ehlo = EHLOMessage.model_validate(body)
    except Exception as exc:
        return 400, {"error": f"invalid_ehlo: {exc}"}

    def mint() -> dict[str, object]:
        activate = agent.activate(ehlo)
        result: dict[str, object] = activate.model_dump()
        result["signature"] = sign_pss(private_key_pem, activate.instance_id)
        return result

    try:
        if replay is None:
            return 200, mint()
        return 200, replay.answer(ehlo.ephemeral_boot_id, ehlo.agent_type, mint)
    except ValueError as exc:
        return 422, {"error": str(exc)}


class EhloServer(socketserver.ThreadingTCPServer):
    """A daemon thread per request: one slow activation holds no other (MST-ORD-03)."""

    daemon_threads = True
    allow_reuse_address = True
    replay: ActivationReplay


def _handler(
    agent: MasterAgent, key_pem: str, replay: ActivationReplay
) -> type[http.server.BaseHTTPRequestHandler]:
    class _Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *_: object) -> None:
            pass

        def _send(self, status: int, body: dict[str, object]) -> None:
            payload = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self) -> None:
            if self.path in ("/health", "/metrics"):
                status, body = handle_health()
            else:
                status, body = 404, {"error": "not_found"}
            self._send(status, body)

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            try:
                body = json.loads(raw)
            except ValueError:
                self._send(400, {"error": "bad_json"})
                return
            if self.path == "/ehlo":
                status, resp = handle_ehlo(body, agent, key_pem, replay)
            else:
                status, resp = 404, {"error": "not_found"}
            self._send(status, resp)

    return _Handler


def build_server(
    host: str,
    port: int,
    agent: MasterAgent,
    key_pem: str,
    *,
    replay: ActivationReplay,
    backlog: int,
) -> EhloServer:
    """Bind and listen (backlog *backlog*) without serving; port 0 picks a free port."""
    server = EhloServer((host, port), _handler(agent, key_pem, replay), False)
    server.request_queue_size = backlog
    server.replay = replay
    try:
        server.server_bind()
        server.server_activate()
    except BaseException:
        server.server_close()
        raise
    return server


def serve(
    port: int,
    agent: MasterAgent,
    key_pem: str,
    settings: MasterSettings,
    host: str = "",
) -> None:
    """Serve EHLO on *host*:*port* until the process ends (the container's loop)."""
    replay = ActivationReplay(replay_lifetime_seconds(settings))
    server = build_server(
        host, port, agent, key_pem, replay=replay, backlog=settings.ehlo_listen_backlog
    )
    with server:
        server.serve_forever()
