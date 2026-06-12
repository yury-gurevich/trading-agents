"""Extended CLI command handlers for narrative display and approval.

Agent: surfaces
Role: implement narrative and approve sub-commands behind the argparse glue.
External I/O: MessageBus calls through the injected surface context.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.common import Provenance
from contracts.operator import CommandResult, HumanCommand, TypedIntent
from contracts.supervisor import DispatchResult
from kernel import AgentMessage
from surfaces.queries.lifecycle import narratives_for_run
from surfaces.render import render_narratives
from surfaces.render_review import render_approve

if TYPE_CHECKING:
    import argparse

    from surfaces.context import SurfaceContext


def cmd_narrative(args: argparse.Namespace, ctx: SurfaceContext) -> str:
    """Render trade narratives for one dispatcher run."""
    run_id = str(args.run_id)
    return render_narratives(narratives_for_run(ctx.graph, run_id), run_id)


def cmd_approve(args: argparse.Namespace, ctx: SurfaceContext) -> str:
    """Approve one pending human-review flag by subject reference."""
    subject = str(args.subject)
    result = _interpret(ctx, f"approve {subject}")
    if result.intent is None or result.intent.family != "approve":
        return f"could not interpret approve command for: {subject}"
    intent = result.intent.model_copy(
        update={
            "parameters": {
                **result.intent.parameters,
                "confirmed": "true",
                "subject": subject,
            }
        }
    )
    return render_approve(_dispatch_intent(ctx, intent), subject)


def cmd_stage_promote(args: argparse.Namespace, ctx: SurfaceContext) -> str:
    """Request execution-stage promotion through the supervisor gate."""
    target = str(args.target)
    intent = TypedIntent(
        family="stage",
        parameters={
            "stage": target,
            "confirmed": "true" if args.confirmed else "",
        },
        requires_confirmation=True,
        provenance=Provenance(run_id=f"stage:{target}", source_agent="cli"),
    )
    result = _dispatch_intent(ctx, intent)
    if result.accepted:
        return f"stage promotion dispatched to {result.routed_to}"
    return f"refused: {result.rejection}"


def _interpret(ctx: SurfaceContext, text: str) -> CommandResult:
    response = ctx.bus.request(
        AgentMessage(
            sender="cli",
            recipient="operator",
            message_type="request",
            capability="interpret",
            payload=HumanCommand(
                text=text,
                actor="cli",
                channel="dashboard",
            ).model_dump(mode="json"),
        )
    )
    return CommandResult.model_validate(response.payload)


def _dispatch_intent(ctx: SurfaceContext, intent: TypedIntent) -> DispatchResult:
    response = ctx.bus.request(
        AgentMessage(
            sender="cli",
            recipient="supervisor",
            message_type="request",
            capability="dispatch_intent",
            payload=intent.model_dump(mode="json"),
        )
    )
    return DispatchResult.model_validate(response.payload)
