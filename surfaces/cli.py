"""Command-line operator surface.

Agent: surfaces
Role: expose status, runs, positions, and command dispatch from the terminal.
External I/O: stdout and optional runtime context construction.
"""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING

from surfaces import cli_commands, cli_commands_extra, cli_commands_queries
from surfaces.context import SurfaceContext, paper_context

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
    position = sub.add_parser("position")
    position.add_argument("pos_id")
    sub.add_parser("flags")
    sub.add_parser("incidents")
    sub.add_parser("proposals")
    sub.add_parser("packs")
    sub.add_parser("datasets")
    stage = sub.add_parser("stage")
    stage_sub = stage.add_subparsers(dest="stage_command")
    promote = stage_sub.add_parser("promote")
    promote.add_argument("target")
    promote.add_argument("--confirmed", action="store_true")
    explain = sub.add_parser("explain")
    explain.add_argument("pos_id")
    narrative = sub.add_parser("narrative")
    narrative.add_argument("run_id")
    approve = sub.add_parser("approve")
    approve.add_argument("subject")
    command = sub.add_parser("command")
    command.add_argument("text")
    return parser


def _dispatch(args: argparse.Namespace, ctx: SurfaceContext) -> str:
    if args.command == "status":
        return cli_commands.cmd_status(args, ctx)
    if args.command == "runs":
        return cli_commands.cmd_runs(args, ctx)
    if args.command == "run":
        return cli_commands.cmd_run(args, ctx)
    if args.command == "positions":
        return cli_commands.cmd_positions(args, ctx)
    if args.command == "position":
        return cli_commands.cmd_position(args, ctx)
    if args.command == "flags":
        return cli_commands.cmd_flags(args, ctx)
    if args.command == "incidents":
        return cli_commands.cmd_incidents(args, ctx)
    if args.command == "proposals":
        return cli_commands_queries.cmd_proposals(args, ctx)
    if args.command == "packs":
        return cli_commands_queries.cmd_packs(args, ctx)
    if args.command == "datasets":
        return cli_commands_queries.cmd_datasets(args, ctx)
    if args.command == "stage" and args.stage_command == "promote":
        return cli_commands_extra.cmd_stage_promote(args, ctx)
    if args.command == "stage":
        return cli_commands_queries.cmd_stage(args, ctx)
    if args.command == "explain":
        return cli_commands_queries.cmd_explain(args, ctx)
    if args.command == "narrative":
        return cli_commands_extra.cmd_narrative(args, ctx)
    if args.command == "approve":
        return cli_commands_extra.cmd_approve(args, ctx)
    return cli_commands.cmd_command(args, ctx)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
