"""MCP surface tests.

Agent: surfaces
Role: verify MCP tool bindings without a live MCP client.
External I/O: none.
"""

from __future__ import annotations

import asyncio

from mcp import types

from kernel import FakeLLMClient, InMemoryGraphStore, InProcessBus
from surfaces.context import SurfaceContext
from surfaces.context import test_context as build_context
from surfaces.mcp_server import TOOLS, list_tools, server
from surfaces.mcp_tools import dispatch_tool


def test_command_tool_requires_explicit_confirmation() -> None:
    ctx = build_context(llm=_run_llm())

    first = dispatch_tool(ctx, "command", {"text": "run the daily scan"})
    second = dispatch_tool(
        ctx, "command", {"text": "run the daily scan", "confirmed": True}
    )

    assert first["accepted"] is False
    assert "confirmation required" in str(first["reason"])
    assert second["accepted"] is True
    assert second["routed_to"] == "orchestration.execute_run"


def test_command_tool_refusal_returns_reason() -> None:
    ctx = build_context(
        llm=FakeLLMClient({"unsafe": '{"outcome":"refused","reason":"unsafe"}'})
    )

    result = dispatch_tool(ctx, "command", {"text": "unsafe command"})

    assert result["accepted"] is False
    assert result["reason"] == "unsafe"


def test_status_and_runs_tools_return_json_dicts() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node(
        "Message",
        "run-a:scan",
        {"run_id": "run-a", "step": "scan", "created_at": "2026-06-11"},
    )
    ctx = build_context(graph=graph)

    status = dispatch_tool(ctx, "status", {})
    runs = dispatch_tool(ctx, "runs", {"limit": 1})

    assert {"healthy", "open_incidents", "pending_flags"} <= set(status)
    assert runs["runs"] == [{"run_id": "run-a", "completed": False, "steps": 1}]


def test_incidents_and_explain_tools_return_seeded_data() -> None:
    graph = InMemoryGraphStore()
    _seed_fault(graph)
    graph.merge_node("Position", "run-a:AAPL", {"run_id": "run-a", "ticker": "AAPL"})
    ctx = build_context(graph=graph)

    incidents = dispatch_tool(ctx, "incidents", {})
    narrative = dispatch_tool(ctx, "explain", {"position_id": "run-a:AAPL"})
    incident_items = incidents["incidents"]

    assert isinstance(incident_items, list)
    assert incident_items[0]["agent"] == "analyst"
    assert narrative["position_id"] == "run-a:AAPL"
    assert narrative["summary"]
    assert narrative["evidence_refs"] == ["reporter.graph"]


def test_error_paths_and_tool_catalog() -> None:
    ctx = build_context()
    unbound = SurfaceContext(InMemoryGraphStore(), InProcessBus())

    assert "unknown tool" in str(dispatch_tool(ctx, "missing", {})["error"])
    bad_limit = dispatch_tool(ctx, "runs", {"limit": "bad"})
    wrong_type_limit = dispatch_tool(ctx, "runs", {"limit": []})
    assert "invalid literal" in str(bad_limit["error"])
    assert wrong_type_limit["error"] == "limit must be an integer"
    assert "narrative not available" in str(
        dispatch_tool(unbound, "explain", {"position_id": "missing"})["error"]
    )
    assert {tool.name for tool in TOOLS} == {
        "command",
        "status",
        "runs",
        "incidents",
        "explain",
    }
    assert asyncio.run(list_tools()).tools == TOOLS


def test_tool_request_handlers_are_registered_on_the_server() -> None:
    """mcp 2.0 replaced the decorators with explicit handler registration.

    The 1.x `@server.list_tools()` / `@server.call_tool()` decorators no longer
    exist, so a silently unregistered method would leave the surface answering
    nothing at runtime while every other test still passed.
    """
    listing = server.get_request_handler("tools/list")
    calling = server.get_request_handler("tools/call")

    assert listing is not None
    assert calling is not None
    assert listing.params_type is types.PaginatedRequestParams
    assert calling.params_type is types.CallToolRequestParams


def _seed_fault(graph: InMemoryGraphStore) -> None:
    graph.merge_node(
        "Fault",
        "fault:analyst:mcp",
        {
            "source_agent": "analyst",
            "capability": "analyze",
            "severity": "critical",
            "message": "analysis failed",
            "occurred_at": "2026-06-11T00:00:00+00:00",
        },
    )


def _run_llm() -> FakeLLMClient:
    return FakeLLMClient({"run": '{"outcome":"intent","family":"run","parameters":{}}'})
