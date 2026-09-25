"""Synchronous MCP tool handler implementations.

Agent: surfaces
Role: implement MCP tools as JSON-serialisable dict dispatchers.
External I/O: MessageBus calls through the injected surface context.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from contracts.reporter import NarrativeRequest, TradeNarrative
from contracts.supervisor import MasterReport, StatusRequest
from kernel import AgentMessage
from surfaces.operator_tools import command_tool, operator_explanation
from surfaces.performance_tool import performance_tool
from surfaces.plain_errors import plain_error
from surfaces.queries.faults import open_faults
from surfaces.queries.fleet_check import (
    LAST_CHECK_HORIZON_MINUTES,
    readiness_override,
)
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
        "performance": performance_tool,
    }
    handler = handlers.get(name)
    if handler is None:
        return {"error": f"unknown tool: {name}"}
    try:
        result = handler(ctx, arguments)
    except Exception as exc:
        return {"error": plain_error(str(exc))}
    if "error" in result:
        return {**result, "error": plain_error(str(result["error"]))}
    return result


def _cmd_status(ctx: SurfaceContext, args: ToolResult) -> ToolResult:
    del args
    report = MasterReport.model_validate(
        _request(
            ctx, "supervisor", "system_status", StatusRequest().model_dump()
        ).payload
    )
    # Health counts faults and flags; a failing fleet check writes neither, so
    # status would read green over a run the dispatcher is about to hold (DL-212).
    fleet = readiness_override(
        ctx.graph,
        now=datetime.now(tz=UTC),
        max_age_minutes=LAST_CHECK_HORIZON_MINUTES,
    )
    summary = report.summary.summary
    if fleet is not None:
        summary = f"{fleet['summary']}.\n{summary}"
    return {
        "healthy": report.healthy,
        "open_incidents": report.open_incidents,
        "pending_flags": report.pending_human_flags,
        "last_run": report.last_successful_run,
        "fleet_check": fleet["state"] if fleet is not None else "passing",
        "summary": summary,
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
                "occurrence_count": fault.occurrence_count,
                "suppressed_count": fault.suppressed_count,
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
