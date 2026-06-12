"""Read-only CLI query command handlers.

Agent: surfaces
Role: implement read-only sub-commands behind the argparse glue.
External I/O: MessageBus calls through the injected surface context.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.reporter import NarrativeRequest, TradeNarrative
from kernel import AgentMessage
from surfaces.queries.datasets import all_datasets
from surfaces.queries.packs import all_packs
from surfaces.queries.proposals import all_proposals
from surfaces.queries.stage import current_stage, stage_history
from surfaces.render import render_packs, render_stage
from surfaces.render_extras import render_datasets, render_explain
from surfaces.render_review import render_proposals

if TYPE_CHECKING:
    import argparse

    from surfaces.context import SurfaceContext


def cmd_proposals(args: argparse.Namespace, ctx: SurfaceContext) -> str:
    """Render researcher proposals."""
    del args
    return render_proposals(all_proposals(ctx.graph))


def cmd_stage(args: argparse.Namespace, ctx: SurfaceContext) -> str:
    """Render execution stage status and history."""
    del args
    return render_stage(current_stage(ctx.graph), stage_history(ctx.graph))


def cmd_packs(args: argparse.Namespace, ctx: SurfaceContext) -> str:
    """Render registered market packs."""
    del args
    return render_packs(all_packs(ctx.pack_registry))


def cmd_datasets(args: argparse.Namespace, ctx: SurfaceContext) -> str:
    """Render curated datasets."""
    del args
    return render_datasets(all_datasets(ctx.graph))


def cmd_explain(args: argparse.Namespace, ctx: SurfaceContext) -> str:
    """Render an on-demand trade narrative for one position."""
    pos_id = str(args.pos_id)
    response = ctx.bus.request(
        AgentMessage(
            sender="cli",
            recipient="reporter",
            message_type="request",
            capability="narrative",
            payload=NarrativeRequest(position_id=pos_id).model_dump(mode="json"),
        )
    )
    if response.message_type == "error":
        return f"explain failed for position: {pos_id}"
    narrative = TradeNarrative.model_validate(response.payload)
    return render_explain(narrative)
