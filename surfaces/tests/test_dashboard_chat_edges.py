"""Dashboard chat error-branch and bounded-dispatch coverage.

Agent: surfaces
Role: prove chat validation, adapter failures, and existing tool edge paths.
External I/O: none; all collaborators are in-memory fakes.
"""

from __future__ import annotations

import json
from io import BytesIO
from typing import TYPE_CHECKING

from agents.operator.llm_anthropic import ConfigurationError
from kernel import FakeLLMClient, InMemoryGraphStore, InProcessBus
from surfaces.context import SurfaceContext, build_test_context
from surfaces.dashboard import build_app, chat_binding
from surfaces.dashboard.chat import _quick_result, _turn, handle_chat
from surfaces.mcp_tools import dispatch_tool
from surfaces.operator_tools import operator_explanation
from surfaces.tests.test_dashboard_app import invoke

if TYPE_CHECKING:
    import pytest


def test_chat_validation_and_result_error_branches() -> None:
    context = build_test_context()
    assert handle_chat({"REQUEST_METHOD": "POST"}, context)[0] == 400
    assert (
        handle_chat(
            {
                "REQUEST_METHOD": "POST",
                "CONTENT_LENGTH": "not-an-integer",
                "wsgi.input": BytesIO(b"{}"),
            },
            context,
        )[0]
        == 400
    )
    missing_run = _body({"message": "hello"})
    assert handle_chat(missing_run, context)[0] == 400
    invalid_request_id = _body({"message": "hello", "run_id": "r", "request_id": 1})
    assert handle_chat(invalid_request_id, context)[0] == 400
    assert _quick_result("status", {"error": "status down"}) == {
        "outcome": "refused",
        "message": "status down",
    }
    assert _turn({"error": "turn down"}, "r")["message"] == "turn down"


def test_incident_quick_ask_renders_rows() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node(
        "Fault",
        "fault:chat",
        {
            "source_agent": "analyst",
            "capability": "analyze",
            "severity": "critical",
            "message": "analysis failed",
            "occurred_at": "2026-07-12T00:00:00+00:00",
        },
    )
    app = build_app(graph, chat_context=build_test_context(graph=graph))
    payload = json.dumps({"message": "Open incidents", "run_id": "r"}).encode()
    result = json.loads(invoke(app, "/api/chat", "POST", payload)[2])
    assert "critical: analysis failed" in result["turn"]["message"]


def test_operator_tool_status_invalid_channel_and_explain_error() -> None:
    status_llm = FakeLLMClient(
        {"status": '{"outcome":"intent","family":"status","parameters":{}}'}
    )
    context = build_test_context(llm=status_llm)
    status = dispatch_tool(context, "command", {"text": "status"})
    invalid = dispatch_tool(
        context, "command", {"text": "status", "channel": "unknown"}
    )
    unbound = SurfaceContext(InMemoryGraphStore(), InProcessBus())

    assert status["outcome"] == "answer"
    assert invalid["error"] == "unsupported command channel: unknown"
    assert "error" in operator_explanation(unbound, "why", "r")


def test_chat_binding_configuration_failure_is_disconnected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(**_kwargs: object) -> object:
        raise ConfigurationError("adapter unavailable")

    monkeypatch.setattr(chat_binding, "AnthropicLLMClient", fail)
    result = chat_binding.bind_dashboard_chat(
        InMemoryGraphStore(),
        {
            "ANTHROPIC_API_KEY": "test-key",  # pragma: allowlist secret
            "POSTGRES_DSN": "bound",
        },
    )
    assert result is None


def _body(payload: object) -> dict[str, object]:
    body = json.dumps(payload).encode()
    return {
        "REQUEST_METHOD": "POST",
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": BytesIO(body),
    }
