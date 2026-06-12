"""CLI command handler implementations.

Agent: surfaces
Role: implement each CLI sub-command behind the argparse glue.
External I/O: MessageBus calls through the injected surface context.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.operator import CommandResult, HumanCommand
from contracts.reporter import RunSnapshot
from contracts.supervisor import DispatchResult, MasterReport, StatusRequest
from kernel import AgentMessage
from surfaces.queries.faults import open_faults
from surfaces.queries.flags import pending_flags
from surfaces.queries.lifecycle import position_lifecycle
from surfaces.queries.positions import open_positions
from surfaces.queries.runs import recent_runs, run_detail
from surfaces.render import (
    render_command,
    render_flags,
    render_lifecycle,
    render_positions,
    render_run_detail,
    render_runs,
    render_status,
)
from surfaces.render_extras import render_incidents

if TYPE_CHECKING:
    import argparse

    from surfaces.context import SurfaceContext


def cmd_status(args: argparse.Namespace, ctx: SurfaceContext) -> str:
    """Render supervisor system status."""
    del args
    return render_status(_status(ctx))


def cmd_runs(args: argparse.Namespace, ctx: SurfaceContext) -> str:
    """Render recent dispatcher runs."""
    return render_runs(recent_runs(ctx.graph, limit=args.limit))


def cmd_run(args: argparse.Namespace, ctx: SurfaceContext) -> str:
    """Render one dispatcher run."""
    run_id = str(args.run_id)
    run = run_detail(ctx.graph, run_id)
    if run is None:
        return f"run {run_id} not found"
    snapshot = ctx.graph.get_node("Snapshot", f"snapshot:{run_id}")
    report = None if snapshot is not None else _report(ctx, run_id)
    return render_run_detail(run, report)


def cmd_positions(args: argparse.Namespace, ctx: SurfaceContext) -> str:
    """Render open positions."""
    del args
    return render_positions(open_positions(ctx.graph))


def cmd_position(args: argparse.Namespace, ctx: SurfaceContext) -> str:
    """Render full lifecycle for one position."""
    pos_id = str(args.pos_id)
    lifecycle = position_lifecycle(ctx.graph, pos_id)
    if lifecycle is None:
        return f"position not found: {pos_id}"
    return render_lifecycle(lifecycle)


def cmd_flags(args: argparse.Namespace, ctx: SurfaceContext) -> str:
    """Render pending human-review flags."""
    del args
    return render_flags(pending_flags(ctx.graph))


def cmd_incidents(args: argparse.Namespace, ctx: SurfaceContext) -> str:
    """Render open incidents."""
    del args
    return render_incidents(open_faults(ctx.graph))


def cmd_command(args: argparse.Namespace, ctx: SurfaceContext) -> str:
    """Interpret one human command and render supervisor routing."""
    result = _interpret(ctx, str(args.text))
    dispatch = None if result.intent is None else _supervise(ctx, result)
    return render_command(result, dispatch)


def _status(ctx: SurfaceContext) -> MasterReport:
    response = ctx.bus.request(
        AgentMessage(
            sender="cli",
            recipient="supervisor",
            message_type="request",
            capability="system_status",
            payload=StatusRequest().model_dump(mode="json"),
        )
    )
    return MasterReport.model_validate(response.payload)


def _report(ctx: SurfaceContext, run_id: str) -> RunSnapshot | None:
    response = ctx.bus.request(
        AgentMessage(
            sender="cli",
            recipient="reporter",
            message_type="request",
            capability="report",
            payload={"run_id": run_id},
        )
    )
    if response.message_type == "error":
        return None
    return RunSnapshot.model_validate(response.payload)


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


def _supervise(ctx: SurfaceContext, result: CommandResult) -> DispatchResult:
    assert result.intent is not None
    response = ctx.bus.request(
        AgentMessage(
            sender="cli",
            recipient="supervisor",
            message_type="request",
            capability="dispatch_intent",
            payload=result.intent.model_dump(mode="json"),
        )
    )
    return DispatchResult.model_validate(response.payload)
