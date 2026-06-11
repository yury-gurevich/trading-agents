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
    from surfaces.queries.flags import FlagView
    from surfaces.queries.lifecycle import PositionLifecycle, RunNarrative
    from surfaces.queries.positions import PositionView
    from surfaces.queries.proposals import ProposalView
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


def render_lifecycle(lifecycle: PositionLifecycle) -> str:
    """Render one position lifecycle."""
    return "\n".join(
        (
            f"{'position_id'.ljust(16)}{lifecycle.position_id}",
            f"{'ticker'.ljust(16)}{lifecycle.ticker}",
            f"{'quantity'.ljust(16)}{lifecycle.quantity}",
            f"{'opened_cents'.ljust(16)}{lifecycle.opened_price_cents}",
            f"{'status'.ljust(16)}{lifecycle.status}",
            f"{'close_trigger'.ljust(16)}{lifecycle.close_trigger or 'none'}",
            f"{'run_id'.ljust(16)}{lifecycle.run_id or 'none'}",
            f"{'confidence'.ljust(16)}{_optional(lifecycle.recommendation_confidence)}",
            f"{'narrative'.ljust(16)}{lifecycle.narrative_text or 'none'}",
        )
    )


def render_flags(flags: tuple[FlagView, ...]) -> str:
    """Render pending human-review flags."""
    if not flags:
        return "no pending flags"
    lines = [_row(("subject_ref", "severity", "created_at"))]
    for flag in flags:
        lines.append(_row((flag.subject_ref, flag.severity, flag.created_at)))
    lines.append('Hint: cli command "approve <subject>" to resolve.')
    return "\n".join(lines)


def render_narratives(narratives: tuple[RunNarrative, ...], run_id: str) -> str:
    """Render trade narratives for one dispatcher run."""
    if not narratives:
        return f"no narratives for run {run_id}"
    lines = [f"Trade narratives - {run_id} ({len(narratives)} position(s))"]
    for narrative in narratives:
        ticker = narrative.ticker or "unknown"
        lines.append(f"\n  {ticker}  [{narrative.position_id}]")
        lines.extend(f"    {line}" for line in narrative.summary.splitlines())
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


def render_proposals(proposals: tuple[ProposalView, ...]) -> str:
    """Render researcher proposals and approval status."""
    if not proposals:
        return "no proposals pending review"
    lines = [f"Proposals: {len(proposals)}"]
    for proposal in proposals:
        status = "approved" if proposal.approved else "pending"
        lines.extend(
            (
                f"\n  [{proposal.proposal_id}] {status} - "
                f"{proposal.change_count} change(s)",
                f"  {proposal.rationale}",
                f"  created: {proposal.created_at}",
            )
        )
    return "\n".join(lines)


def _row(values: tuple[str, ...]) -> str:
    return "  ".join(value.ljust(18) for value in values)


def _optional(value: object | None) -> object:
    return "none" if value is None else value
