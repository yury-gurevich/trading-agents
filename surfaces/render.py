"""Plain-text render helpers for the CLI surface.

Agent: surfaces
Role: convert typed surface DTOs into stable text output.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contracts.operator import CommandResult
    from contracts.reporter import RunSnapshot
    from contracts.supervisor import DispatchResult, MasterReport
    from surfaces.queries.positions import PositionView
    from surfaces.queries.runs import RunSummary


def render_status(report: MasterReport) -> str:
    """Render supervisor health status."""
    return "\n".join(
        (
            f"{'healthy'.ljust(16)}{report.healthy}",
            f"{'open_incidents'.ljust(16)}{report.open_incidents}",
            f"{'pending_flags'.ljust(16)}{report.pending_human_flags}",
            f"{'last_run'.ljust(16)}{report.last_successful_run or 'none'}",
            f"{'summary'.ljust(16)}{report.summary.summary}",
        )
    )


def render_runs(runs: tuple[RunSummary, ...]) -> str:
    """Render a compact dispatcher-run table."""
    if not runs:
        return "no runs"
    lines = [_row(("run_id", "steps", "completed", "snapshot"))]
    for run in runs:
        step_names = ",".join(step.name for step in run.steps)
        lines.append(
            _row(
                (
                    run.run_id,
                    step_names,
                    str(run.completed),
                    str(run.snapshot_available),
                )
            )
        )
    return "\n".join(lines)


def render_run_detail(run: RunSummary, snapshot: RunSnapshot | None) -> str:
    """Render one run plus an optional reporter snapshot."""
    lines = [render_runs((run,))]
    headline = None if snapshot is None else snapshot.headline.summary
    lines.append(f"{'headline'.ljust(16)}{headline or 'snapshot unavailable'}")
    return "\n".join(lines)


def render_positions(positions: tuple[PositionView, ...]) -> str:
    """Render open positions."""
    if not positions:
        return "no open positions"
    lines = [_row(("position_id", "ticker", "qty", "status", "trigger"))]
    for position in positions:
        lines.append(
            _row(
                (
                    position.position_id,
                    position.ticker,
                    str(position.quantity),
                    position.status,
                    position.close_trigger or "",
                )
            )
        )
    return "\n".join(lines)


def render_command(result: CommandResult, dispatch: DispatchResult | None) -> str:
    """Render operator interpretation and supervisor routing."""
    lines = (
        f"{'outcome'.ljust(16)}{result.outcome}",
        f"{'message'.ljust(16)}{result.message.summary}",
    )
    if dispatch is None:
        return "\n".join(lines)
    return "\n".join(
        (
            *lines,
            f"{'accepted'.ljust(16)}{dispatch.accepted}",
            f"{'routed_to'.ljust(16)}{dispatch.routed_to or 'none'}",
            f"{'rejection'.ljust(16)}{dispatch.rejection or 'none'}",
        )
    )


def _row(values: tuple[str, ...]) -> str:
    return "  ".join(value.ljust(18) for value in values)
