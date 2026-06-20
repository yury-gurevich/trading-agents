"""Master HTTP server — EHLO endpoint and health check.

Agent: master
Role: expose /ehlo (ACTIVATE handshake) and /health over HTTP; run as the
      container's main blocking loop.
External I/O: TCP port 8000 (inbound HTTP).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from contracts.master import EHLOMessage
from kernel.crypto import sign_pss

if TYPE_CHECKING:
    from agents.master.agent import MasterAgent


def handle_health() -> tuple[int, dict[str, object]]:
    """Return 200 OK with a status body."""
    return 200, {"status": "ok"}


def handle_ehlo(
    body: dict[str, object],
    agent: MasterAgent,
    private_key_pem: str,
) -> tuple[int, dict[str, object]]:
    """Parse EHLO, call MasterAgent.activate(), sign instance_id, return ACTIVATE."""
    try:
        ehlo = EHLOMessage.model_validate(body)
    except Exception as exc:
        return 400, {"error": f"invalid_ehlo: {exc}"}
    try:
        activate = agent.activate(ehlo)
    except ValueError as exc:
        return 422, {"error": str(exc)}
    result: dict[str, object] = activate.model_dump()
    result["signature"] = sign_pss(private_key_pem, activate.instance_id)
    return 200, result


# ── HTTP wiring — not unit-testable; covered by integration/manual only ────────


def serve(port: int, agent: MasterAgent, key_pem: str) -> None:  # pragma: no cover
    """Start a blocking HTTP server on *port*."""
    import http.server
    import socketserver

    def _make_handler() -> type:
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
                if self.path == "/health" or self.path == "/metrics":
                    status, body = handle_health()
                else:
                    status, body = 404, {"error": "not_found"}
                self._send(status, body)

            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length)
                try:
                    body = json.loads(raw)
                except Exception:
                    self._send(400, {"error": "bad_json"})
                    return
                if self.path == "/ehlo":
                    status, resp = handle_ehlo(body, agent, key_pem)
                else:
                    status, resp = 404, {"error": "not_found"}
                self._send(status, resp)

        return _Handler

    with socketserver.TCPServer(("", port), _make_handler()) as httpd:
        httpd.serve_forever()
