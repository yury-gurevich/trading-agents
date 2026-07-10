"""Dashboard WSGI app tests — routing, JSON, static serving, guards.

Agent: surfaces
Role: verify every route responds, unknown runs/routes 404, non-GET 405,
      static files serve with correct types, and traversal is blocked.
External I/O: none.
"""

from __future__ import annotations

import json
from typing import Any, cast

from kernel import InMemoryGraphStore
from orchestration.start import place_run_request
from surfaces.dashboard import build_app
from surfaces.tests.test_dashboard_projections import cascade_graph

VIEWS = ("verdict", "stages", "flags", "positions", "recovery", "bundle")


def invoke(
    app: Any, path: str, method: str = "GET"
) -> tuple[str, dict[str, str], bytes]:
    captured: dict[str, Any] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        captured["status"] = status
        captured["headers"] = dict(headers)

    body = b"".join(app({"PATH_INFO": path, "REQUEST_METHOD": method}, start_response))
    return captured["status"], captured["headers"], body


def test_runs_list_route() -> None:
    app = build_app(cascade_graph("app-run"))
    status, headers, body = invoke(app, "/api/runs")
    assert status == "200 OK"
    assert headers["Content-Type"].startswith("application/json")
    assert json.loads(body)[0]["run_id"] == "app-run"


def test_every_run_view_responds() -> None:
    app = build_app(cascade_graph("app-run"))
    for view in VIEWS:
        status, _, body = invoke(app, f"/api/runs/app-run/{view}")
        assert status == "200 OK", view
        json.loads(body)


def test_unknown_run_is_404() -> None:
    app = build_app(InMemoryGraphStore())
    status, _, body = invoke(app, "/api/runs/ghost/verdict")
    assert status == "404 Not Found"
    assert "unknown run_id" in cast("str", json.loads(body)["error"])


def test_unknown_view_and_deep_path_are_404() -> None:
    graph = InMemoryGraphStore()
    place_run_request(graph, run_id="r", tickers=("AAPL",))
    app = build_app(graph)
    assert invoke(app, "/api/runs/r/nope")[0] == "404 Not Found"
    assert invoke(app, "/api/runs/r/verdict/extra")[0] == "404 Not Found"


def test_non_get_is_405() -> None:
    app = build_app(InMemoryGraphStore())
    assert invoke(app, "/api/runs", method="POST")[0] == "405 Method Not Allowed"


def test_index_and_assets_serve() -> None:
    app = build_app(InMemoryGraphStore())
    status, headers, body = invoke(app, "/")
    assert status == "200 OK"
    assert headers["Content-Type"].startswith("text/html")
    assert b"trading-agents" in body
    assert invoke(app, "/app.css")[1]["Content-Type"].startswith("text/css")
    assert invoke(app, "/app.js")[0] == "200 OK"


def test_missing_static_and_traversal_are_404() -> None:
    app = build_app(InMemoryGraphStore())
    assert invoke(app, "/nope.txt")[0] == "404 Not Found"
    assert invoke(app, "/../pyproject.toml")[0] == "404 Not Found"
