"""Synchronous MCP tool handler implementations.

Agent: surfaces
Role: implement MCP tools as JSON-serialisable dict dispatchers.
External I/O: MessageBus calls through the injected surface context.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from contracts.reporter import NarrativeRequest, TradeNarrative
from contracts.supervisor import MasterReport, StatusRequest
from kernel import AgentMessage
from surfaces.operator_tools import command_tool, operator_explanation
from surfaces.queries.faults import open_faults
from surfaces.queries.runs import recent_runs

if TYPE_CHECKING:
    from surfaces.context import SurfaceContext

ToolResult = dict[str, object]
ToolHandler = Callable[["SurfaceContext", ToolResult], ToolResult]


def dispatch_tool(ctx: SurfaceContext, name: str, arguments: ToolResult) -> ToolResult:
    """Route one MCP tool call to the appropriate synchronous handler."""
    handlers: dict[str, ToolHandler] = {
        "command": command_tool,
        "status": _cmd_status,
        "runs": _cmd_runs,
        "incidents": _cmd_incidents,
        "explain": _cmd_explain,
    }
    handler = handlers.get(name)
    if handler is None:
        return {"error": f"unknown tool: {name}"}
    try:
        return handler(ctx, arguments)
    except Exception as exc:
        return {"error": str(exc)}


def _cmd_status(ctx: SurfaceContext, args: ToolResult) -> ToolResult:
    del args
    report = MasterReport.model_validate(
        _request(
            ctx, "supervisor", "system_status", StatusRequest().model_dump()
        ).payload
    )
    return {
        "healthy": report.healthy,
        "open_incidents": report.open_incidents,
        "pending_flags": report.pending_human_flags,
        "last_run": report.last_successful_run,
        "summary": report.summary.summary,
    }


def _cmd_runs(ctx: SurfaceContext, args: ToolResult) -> ToolResult:
    raw_limit = args.get("limit", 10)
    if not isinstance(raw_limit, int | str):
        raise ValueError("limit must be an integer")
    runs = recent_runs(ctx.graph, limit=int(raw_limit))
    return {
        "runs": [
            {"run_id": run.run_id, "completed": run.completed, "steps": len(run.steps)}
            for run in runs
        ]
    }


def _cmd_incidents(ctx: SurfaceContext, args: ToolResult) -> ToolResult:
    del args
    return {
        "incidents": [
            {
                "fault_id": fault.fault_id,
                "agent": fault.source_agent,
                "capability": fault.capability,
                "severity": fault.severity,
                "message": fault.message,
            }
            for fault in open_faults(ctx.graph)
        ]
    }


def _cmd_explain(ctx: SurfaceContext, args: ToolResult) -> ToolResult:
    if "subject" in args:
        return operator_explanation(
            ctx,
            str(args["subject"]),
            str(args.get("run_id", "")),
            request_id=str(args.get("request_id", "")) or None,
        )
    position_id = str(args["position_id"])
    response = _request(
        ctx,
        "reporter",
        "narrative",
        NarrativeRequest(position_id=position_id).model_dump(mode="json"),
    )
    if response.message_type == "error":
        return {"error": f"narrative not available for {position_id}"}
    narrative = TradeNarrative.model_validate(response.payload)
    return {
        "position_id": narrative.position_id,
        "summary": narrative.story.summary,
        "evidence_refs": list(narrative.story.evidence_refs),
    }


def _request(
    ctx: SurfaceContext, recipient: str, capability: str, payload: ToolResult
) -> AgentMessage:
    return ctx.bus.request(
        AgentMessage(
            sender="mcp",
            recipient=recipient,
            message_type="request",
            capability=capability,
            payload=payload,
        )
    )
