"""Human-review render helpers.

Agent: surfaces
Role: render approval command output.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contracts.supervisor import DispatchResult
    from surfaces.queries.proposals import ProposalView


def render_approve(result: DispatchResult, subject: str) -> str:
    """Render a single approve command result."""
    if not result.accepted:
        lines = [f"approve refused: {subject}"]
        if result.rejection:
            lines.append(f"  reason: {result.rejection}")
        return "\n".join(lines)
    lines = [f"approved: {subject}"]
    if result.routed_to:
        lines.append(f"  routed_to: {result.routed_to}")
    return "\n".join(lines)


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
