"""Dashboard flag acknowledgement tests.

Agent: surfaces
Role: prove flag acknowledgement routes through audited chat confirmation.
External I/O: none; graph, LLM, and WSGI requests are in-memory fakes.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any, cast

from kernel import InMemoryGraphStore
from orchestration.start import place_run_request
from surfaces.context import build_test_context
from surfaces.dashboard import build_app
from surfaces.tests.test_dashboard_app import invoke

_RUN = "chat-run"
_SUBJECT = "stale-confirm-intent-warning"


def test_flag_acknowledgement_uses_chat_confirmation_and_resolves_flag() -> None:
    graph = InMemoryGraphStore()
    place_run_request(graph, run_id=_RUN, tickers=("AAPL",), as_of=date(2026, 7, 14))
    graph.merge_node(
        "Flag",
        f"flag:{_SUBJECT}:warn",
        {
            "subject_ref": _SUBJECT,
            "severity": "warn",
            "reason": "Confirm the typed resume intent.",
            "status": "pending",
            "created_at": "2026-07-14T01:00:00+00:00",
        },
    )
    app = build_app(
        graph,
        chat_context=build_test_context(graph=graph, llm=_ApproveMisrouteLLM()),
    )

    first = _post(app, f"approve {_SUBJECT}", request_id="ack-one")["turn"]
    assert first["outcome"] == "needs_confirmation"
    assert first["typed_intent"] == {
        "family": "approve",
        "parameters": {"target": _SUBJECT},
        "requires_confirmation": True,
    }
    assert graph.get_node("FlagResolution", f"resolution:flag:{_SUBJECT}:warn") is None

    confirmed = _post(app, f"approve {_SUBJECT}", confirmed=True, request_id="ack-one")[
        "turn"
    ]
    assert confirmed["outcome"] == "confirmed_dispatch"
    assert graph.get_node("FlagResolution", f"resolution:flag:{_SUBJECT}:warn")
    flags = cast(
        "list[dict[str, Any]]",
        json.loads(invoke(app, f"/api/runs/{_RUN}/flags")[2]),
    )
    assert flags[0]["status"] == "resolved"


def test_static_assets_wire_flag_ack_and_warning_links() -> None:
    app_js = _asset("app.js")
    chat_js = _asset("chat.js")
    verdict_js = _asset("verdict.js")

    assert "dashboard:flag-ack" in app_js
    assert "approve " in chat_js
    for code in (
        "pending_flags",
        "degraded_feeds",
        "deploy_behind",
        "deploy_unverified",
        "bus_unverified",
        "bus_unreachable",
        "untracked_spend",
        "acceptance_warning",
    ):
        assert code in verdict_js


def _post(
    app: Any, message: str, *, confirmed: bool = False, request_id: str
) -> dict[str, Any]:
    body = json.dumps(
        {
            "message": message,
            "run_id": _RUN,
            "confirmed": confirmed,
            "request_id": request_id,
        }
    ).encode()
    status, _, payload = invoke(app, "/api/chat", "POST", body)
    assert status == "200 OK"
    return cast("dict[str, Any]", json.loads(payload))


def _asset(name: str) -> str:
    status, _, body = invoke(build_app(InMemoryGraphStore()), f"/{name}")
    assert status == "200 OK"
    return body.decode()


class _ApproveMisrouteLLM:
    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del system, user, tool_schema
        return '{"outcome":"intent","family":"status","parameters":{}}'
