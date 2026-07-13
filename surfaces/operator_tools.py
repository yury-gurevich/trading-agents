"""Bounded operator command helpers shared by MCP and dashboard surfaces.

Agent: surfaces
Role: translate command tool calls into operator and supervisor RPCs.
External I/O: MessageBus calls through the injected SurfaceContext.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.operator.domain.result import request_correlation
from contracts.operator import CommandResult, ExplainRequest, HumanCommand
from contracts.supervisor import DispatchResult, MasterReport, StatusRequest
from kernel import AgentMessage

if TYPE_CHECKING:
    from surfaces.context import SurfaceContext

ToolResult = dict[str, object]


def command_tool(ctx: SurfaceContext, args: ToolResult) -> ToolResult:
    """Interpret one bounded command and apply the supervisor gate."""
    text = str(args["text"])
    actor = str(args.get("actor", "assistant"))
    channel = str(args.get("channel", "mcp"))
    run_id = str(args.get("run_id", ""))
    request_id = str(args.get("request_id", "")) or None
    grounded_text = f"{text}\nSelected run: {run_id}" if run_id else text
    if channel not in ("dashboard", "phone", "mcp"):
        raise ValueError(f"unsupported command channel: {channel}")
    response = _request(
        ctx,
        "operator",
        "interpret",
        HumanCommand(
            text=grounded_text,
            actor=actor,
            channel=channel,  # type: ignore[arg-type]
            request_id=request_id,
        ).model_dump(mode="json"),
    )
    result = CommandResult.model_validate(response.payload)
    audit_id = f"audit:{request_correlation(request_id, actor, channel, grounded_text)}"
    if result.intent is None:
        return {
            "accepted": False,
            "outcome": result.outcome,
            "message": result.message.summary,
            "reason": result.message.summary,
            "audit_id": audit_id,
        }
    intent = result.intent
    typed_intent: ToolResult = {
        "family": intent.family,
        "parameters": dict(intent.parameters),
        "requires_confirmation": intent.requires_confirmation,
    }
    if intent.family == "explain":
        subject = intent.parameters.get("subject") or text
        return operator_explanation(ctx, subject, run_id, request_id=request_id)
    if intent.family == "status":
        return _status_answer(ctx, typed_intent, audit_id)
    if args.get("confirmed") is True:
        intent = intent.model_copy(
            update={"parameters": {**intent.parameters, "confirmed": "true"}}
        )
    dispatch = DispatchResult.model_validate(
        _request(ctx, "supervisor", "dispatch_intent", intent.model_dump()).payload
    )
    outcome = (
        "confirmed_dispatch"
        if dispatch.accepted and args.get("confirmed")
        else ("dispatched" if dispatch.accepted else "refused")
    )
    if intent.requires_confirmation and not args.get("confirmed"):
        outcome = "needs_confirmation"
    return {
        "accepted": dispatch.accepted,
        "outcome": outcome,
        "routed_to": dispatch.routed_to,
        "message": dispatch.rejection or f"Command routed to {dispatch.routed_to}.",
        "reason": dispatch.rejection,
        "typed_intent": typed_intent,
        "audit_id": audit_id,
    }


def operator_explanation(
    ctx: SurfaceContext,
    subject: str,
    run_id: str,
    *,
    request_id: str | None = None,
) -> ToolResult:
    """Ask the operator for a run-grounded explanation."""
    grounded_subject = f"{subject}\nSelected run: {run_id}" if run_id else subject
    response = _request(
        ctx,
        "operator",
        "explain",
        ExplainRequest(subject=grounded_subject, request_id=request_id).model_dump(
            mode="json"
        ),
    )
    if response.message_type == "error":
        return {"error": str(response.payload.get("message", "explanation failed"))}
    summary = str(response.payload.get("summary", "No explanation returned."))
    audit = request_correlation(request_id, "explain", grounded_subject, "operator")
    return {
        "accepted": True,
        "outcome": "answer",
        "message": summary,
        "run_id": run_id,
        "audit_id": f"audit:{audit}",
    }


def _status_answer(
    ctx: SurfaceContext, typed_intent: ToolResult, audit_id: str
) -> ToolResult:
    report = MasterReport.model_validate(
        _request(
            ctx, "supervisor", "system_status", StatusRequest().model_dump()
        ).payload
    )
    return {
        "accepted": True,
        "outcome": "answer",
        "message": report.summary.summary,
        "typed_intent": typed_intent,
        "audit_id": audit_id,
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
