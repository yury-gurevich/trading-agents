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
import re
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs

from surfaces.dashboard import projections, projections_state
from surfaces.dashboard.bundle_azure import container_logs
from surfaces.dashboard.projections_fleet import fleet_projection
from surfaces.dashboard.projections_infra import infra_projection
from surfaces.dashboard.projections_vitals import vitals_projection
from surfaces.dashboard.settings import DashboardSettings

if TYPE_CHECKING:
    from kernel import GraphStore
    from surfaces.dashboard.azure_port import AzureReader

_STATIC = Path(__file__).parent / "static"

_RUN_VIEWS: dict[str, Callable[[GraphStore, str], object]] = {
    "verdict": projections.run_verdict,
    "stages": lambda g, r: projections.run_stages(g, r),
    "flags": lambda g, r: projections_state.run_flags(g, r),
    "positions": projections_state.run_positions,
    "recovery": projections_state.run_recovery,
}

_CONTAINER = re.compile(r"[a-z0-9][a-z0-9-]{0,62}")

StartResponse = Callable[..., Any]


def build_app(
    graph: GraphStore,
    azure: AzureReader | None = None,
    settings: DashboardSettings | None = None,
) -> Callable[..., list[bytes]]:
    """Return the WSGI app over injected graph and optional Azure readers."""
    config = settings or DashboardSettings()

    def _app(environ: dict[str, Any], start_response: StartResponse) -> list[bytes]:
        path = str(environ.get("PATH_INFO", "/"))
        query = parse_qs(str(environ.get("QUERY_STRING", "")))
        if str(environ.get("REQUEST_METHOD", "GET")) != "GET":
            return _json(start_response, 405, {"error": "GET only"})
        if path == "/api/runs":
            return _json(start_response, 200, projections.list_runs(graph))
        if path == "/api/infra":
            return _json(start_response, 200, infra_projection(graph, azure, config))
        if path == "/api/fleet":
            run_id = _selected_run(graph, query)
            return _json(
                start_response, 200, fleet_projection(graph, azure, config, run_id)
            )
        if path == "/api/vitals":
            vital_run = query.get("run_id", [None])[0]
            return _json(
                start_response,
                200,
                vitals_projection(graph, azure, config, vital_run),
            )
        if path.startswith("/api/containers/"):
            return _container_view(path, query, azure, config, start_response)
        if path.startswith("/api/runs/"):
            return _run_view(graph, azure, config, path, start_response)
        return _static(path, start_response)

    return _app


def _run_view(
    graph: GraphStore,
    azure: AzureReader | None,
    settings: DashboardSettings,
    path: str,
    start_response: StartResponse,
) -> list[bytes]:
    parts = path.removeprefix("/api/runs/").split("/")
    if len(parts) != 2 or parts[1] not in (*_RUN_VIEWS, "bundle"):
        return _json(start_response, 404, {"error": f"unknown route {path}"})
    run_id, view = parts
    if projections.run_request_node(graph, run_id) is None:
        return _json(start_response, 404, {"error": f"unknown run_id {run_id}"})
    if view == "bundle":
        payload = projections_state.run_bundle(graph, run_id, azure, settings)
        return _json(start_response, 200, payload)
    return _json(start_response, 200, _RUN_VIEWS[view](graph, run_id))


def _container_view(
    path: str,
    query: dict[str, list[str]],
    azure: AzureReader | None,
    settings: DashboardSettings,
    start_response: StartResponse,
) -> list[bytes]:
    parts = path.removeprefix("/api/containers/").split("/")
    if len(parts) != 2 or parts[1] != "logs" or not _CONTAINER.fullmatch(parts[0]):
        return _json(start_response, 404, {"error": f"unknown route {path}"})
    raw = query.get("tail", [str(settings.log_tail_default)])[0]
    try:
        requested = int(raw)
    except ValueError:
        requested = settings.log_tail_default
    tail = max(1, min(requested, settings.log_tail_max))
    payload = container_logs(azure, settings, parts[0], tail)
    return _json(start_response, 200, payload)


def _selected_run(graph: GraphStore, query: dict[str, list[str]]) -> str:
    supplied = query.get("run_id", [""])[0]
    if supplied:
        return supplied
    rows = projections.list_runs(graph)
    return str(rows[0]["run_id"]) if rows else ""


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
