"""Dashboard WSGI app — JSON read-model API + static frontend.

Agent: surfaces
Role: route /api/runs* to the projections and serve the static frontend;
      pure WSGI (same pattern as metrics_server), reads-only over the injected
      GraphStore. Surfaces never drive an agent.
External I/O: none (the caller binds it to a server).
"""

from __future__ import annotations

import json
import mimetypes
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from surfaces.dashboard import projections, projections_state

if TYPE_CHECKING:
    from kernel import GraphStore

_STATIC = Path(__file__).parent / "static"

_RUN_VIEWS: dict[str, Callable[[GraphStore, str], object]] = {
    "verdict": projections.run_verdict,
    "stages": lambda g, r: projections.run_stages(g, r),
    "flags": lambda g, r: projections_state.run_flags(g, r),
    "positions": projections_state.run_positions,
    "recovery": projections_state.run_recovery,
    "bundle": projections_state.run_bundle,
}

StartResponse = Callable[..., Any]


def build_app(graph: GraphStore) -> Callable[..., list[bytes]]:
    """Return the WSGI app over one injected GraphStore."""

    def _app(environ: dict[str, Any], start_response: StartResponse) -> list[bytes]:
        path = str(environ.get("PATH_INFO", "/"))
        if str(environ.get("REQUEST_METHOD", "GET")) != "GET":
            return _json(start_response, 405, {"error": "GET only"})
        if path == "/api/runs":
            return _json(start_response, 200, projections.list_runs(graph))
        if path.startswith("/api/runs/"):
            return _run_view(graph, path, start_response)
        return _static(path, start_response)

    return _app


def _run_view(
    graph: GraphStore, path: str, start_response: StartResponse
) -> list[bytes]:
    parts = path.removeprefix("/api/runs/").split("/")
    if len(parts) != 2 or parts[1] not in _RUN_VIEWS:
        return _json(start_response, 404, {"error": f"unknown route {path}"})
    run_id, view = parts
    if projections.run_request_node(graph, run_id) is None:
        return _json(start_response, 404, {"error": f"unknown run_id {run_id}"})
    return _json(start_response, 200, _RUN_VIEWS[view](graph, run_id))


def _json(start_response: StartResponse, status: int, payload: object) -> list[bytes]:
    body = json.dumps(payload).encode("utf-8")
    reason = {200: "OK", 404: "Not Found", 405: "Method Not Allowed"}[status]
    start_response(
        f"{status} {reason}",
        [("Content-Type", "application/json; charset=utf-8")],
    )
    return [body]


def _static(path: str, start_response: StartResponse) -> list[bytes]:
    name = "index.html" if path == "/" else path.lstrip("/")
    target = (_STATIC / name).resolve()
    if not target.is_relative_to(_STATIC.resolve()) or not target.is_file():
        return _json(start_response, 404, {"error": f"not found {path}"})
    content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
    start_response("200 OK", [("Content-Type", content_type)])
    return [target.read_bytes()]
