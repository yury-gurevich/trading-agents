"""Command-line operator surface.

Agent: surfaces
Role: expose status, runs, positions, and command dispatch from the terminal.
External I/O: stdout and optional runtime context construction.
"""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING

from contracts.operator import CommandResult, HumanCommand
from contracts.reporter import RunSnapshot
from contracts.supervisor import DispatchResult, MasterReport, StatusRequest
from kernel import AgentMessage
from surfaces.context import SurfaceContext, paper_context
from surfaces.queries.positions import open_positions
from surfaces.queries.runs import recent_runs, run_detail
from surfaces.render import (
    render_command,
    render_positions,
    render_run_detail,
    render_runs,
    render_status,
)

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import TextIO


def main(
    argv: Sequence[str] | None = None,
    *,
    context: SurfaceContext | None = None,
    stdout: TextIO | None = None,
) -> int:
    """Run the CLI and return a process-style exit code."""
    args = _parser().parse_args(argv)
    ctx = context if context is not None else paper_context()
    out = stdout if stdout is not None else sys.stdout
    text = _dispatch(args, ctx)
    out.write(f"{text}\n")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="surfaces")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    runs = sub.add_parser("runs")
    runs.add_argument("--limit", type=int, default=10)
    run = sub.add_parser("run")
    run.add_argument("run_id")
    sub.add_parser("positions")
    command = sub.add_parser("command")
    command.add_argument("text")
    return parser


def _dispatch(args: argparse.Namespace, ctx: SurfaceContext) -> str:
    if args.command == "status":
        return render_status(_status(ctx))
    if args.command == "runs":
        return render_runs(recent_runs(ctx.graph, limit=args.limit))
    if args.command == "run":
        return _run(ctx, str(args.run_id))
    if args.command == "positions":
        return render_positions(open_positions(ctx.graph))
    return _command(ctx, str(args.text))


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


def _run(ctx: SurfaceContext, run_id: str) -> str:
    run = run_detail(ctx.graph, run_id)
    if run is None:
        return f"run {run_id} not found"
    snapshot = ctx.graph.get_node("Snapshot", f"snapshot:{run_id}")
    report = None if snapshot is not None else _report(ctx, run_id)
    return render_run_detail(run, report)


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


def _command(ctx: SurfaceContext, text: str) -> str:
    result = _interpret(ctx, text)
    dispatch = None if result.intent is None else _supervise(ctx, result)
    return render_command(result, dispatch)


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


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
