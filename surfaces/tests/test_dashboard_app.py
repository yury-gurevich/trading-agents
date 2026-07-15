"""Dashboard WSGI app tests — routing, JSON, static serving, guards.

Agent: surfaces
Role: verify every route responds, unknown runs/routes 404, non-GET 405,
      static files serve with correct types, and traversal is blocked.
External I/O: none.
"""

from __future__ import annotations

import json
from io import BytesIO
from typing import Any, cast
from urllib.parse import urlsplit

from kernel import InMemoryGraphStore
from orchestration.start import place_run_request
from surfaces.dashboard import build_app
from surfaces.tests.dashboard_fakes import FakeAzureReader
from surfaces.tests.test_dashboard_costs import _settings
from surfaces.tests.test_dashboard_projections import cascade_graph

VIEWS = ("verdict", "stages", "flags", "positions", "recovery", "bundle")


def invoke(
    app: Any, path: str, method: str = "GET", body: bytes = b""
) -> tuple[str, dict[str, str], bytes]:
    captured: dict[str, Any] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        captured["status"] = status
        captured["headers"] = dict(headers)

    parsed = urlsplit(path)
    body = b"".join(
        app(
            {
                "PATH_INFO": parsed.path,
                "QUERY_STRING": parsed.query,
                "REQUEST_METHOD": method,
                "CONTENT_LENGTH": str(len(body)),
                "wsgi.input": BytesIO(body),
            },
            start_response,
        )
    )
    return captured["status"], captured["headers"], body


def test_runs_list_route() -> None:
    app = build_app(cascade_graph("app-run"))
    status, headers, body = invoke(app, "/api/runs")
    assert status == "200 OK"
    assert headers["Content-Type"].startswith("application/json")
    assert json.loads(body)[0]["run_id"] == "app-run"


def test_master_verdict_route_uses_run_query() -> None:
    app = build_app(cascade_graph("app-run"), FakeAzureReader(), _settings())
    status, _, body = invoke(app, "/api/verdict?run=app-run")
    assert status == "200 OK"
    payload = json.loads(body)
    assert payload["run_id"] == "app-run"
    assert payload["light"] in {"RED", "GREEN"}
    missing = json.loads(invoke(app, "/api/verdict?run=ghost")[2])
    assert missing["light"] == "RED"
    assert "provider" in missing["summary"]
    empty_status, _, empty_body = invoke(
        build_app(InMemoryGraphStore()), "/api/verdict"
    )
    assert empty_status == "404 Not Found"
    assert json.loads(empty_body)["error"] == "no run_id available"


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
    assert b"verdict-hero" in body
    assert b"/chat.css?v=125-1" in body
    assert b"/chat.js?v=125-1" in body
    assert invoke(app, "/app.css")[1]["Content-Type"].startswith("text/css")
    assert invoke(app, "/app.js")[0] == "200 OK"
    assert invoke(app, "/infra.js")[0] == "200 OK"
    assert invoke(app, "/verdict.css")[0] == "200 OK"
    assert invoke(app, "/verdict.js")[0] == "200 OK"
    assert invoke(app, "/chat.css")[0] == "200 OK"
    assert invoke(app, "/chat.js")[0] == "200 OK"
    assert b"#chat [hidden]" in invoke(app, "/chat.css")[2]
    assert b"resume-action" in invoke(app, "/app.js")[2]
    assert b"resume-wired" in invoke(app, "/chat.js")[2]


def test_missing_static_and_traversal_are_404() -> None:
    app = build_app(InMemoryGraphStore())
    assert invoke(app, "/nope.txt")[0] == "404 Not Found"
    assert invoke(app, "/../pyproject.toml")[0] == "404 Not Found"


def test_s123_routes_use_fake_azure_and_tail_bounds() -> None:
    graph = cascade_graph("app-run")
    azure = FakeAzureReader()
    app = build_app(graph, azure, _settings())
    for path in (
        "/api/infra",
        "/api/fleet?run_id=app-run",
        "/api/vitals?run_id=app-run",
        "/api/containers/execution/logs?tail=9999",
    ):
        status, _, body = invoke(app, path)
        assert status == "200 OK", path
        json.loads(body)
    logs = json.loads(invoke(app, "/api/containers/execution/logs?tail=nope")[2])
    assert logs["tail"] == 200
    assert azure.log_calls[-2][3] == 500
    assert json.loads(invoke(app, "/api/fleet")[2])["run_id"] == "app-run"
    bundle = json.loads(invoke(app, "/api/runs/app-run/bundle")[2])
    assert bundle["logs"]["available"] is True
    assert bundle["images"]["containers"]["execution"]["tag"] == "s123"


def test_s123_degraded_routes_still_return_http_200() -> None:
    graph = cascade_graph("app-run")
    app = build_app(graph, None, _settings())
    infra = json.loads(invoke(app, "/api/infra")[2])
    logs = json.loads(invoke(app, "/api/containers/execution/logs")[2])
    assert infra["available"] is False
    assert logs["available"] is False
    assert invoke(app, "/api/containers/INVALID!/logs")[0] == "404 Not Found"
    empty = build_app(InMemoryGraphStore(), None, _settings())
    assert json.loads(invoke(empty, "/api/fleet")[2])["run_id"] == ""
