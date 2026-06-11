"""Proposal query projections.

Agent: surfaces
Role: read Experiment nodes and project proposal views.
External I/O: GraphStore reads.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from surfaces.queries._graph import nodes_by_label

if TYPE_CHECKING:
    from kernel import GraphStore, Node


@dataclass(frozen=True)
class ProposalView:
    """Operator-facing view of one researcher proposal."""

    proposal_id: str
    change_count: int
    rationale: str
    created_at: str
    approved: bool


def all_proposals(graph: GraphStore) -> tuple[ProposalView, ...]:
    """Return all proposals, newest first."""
    proposals = (_view(graph, node) for node in nodes_by_label(graph, "Experiment"))
    return tuple(sorted(proposals, key=lambda item: item.created_at, reverse=True))


def _view(graph: GraphStore, node: Node) -> ProposalView:
    proposal_id = str(node.props.get("proposal_id", ""))
    return ProposalView(
        proposal_id=proposal_id,
        change_count=int(node.props.get("change_count", 0)),
        rationale=str(node.props.get("rationale_summary", "")),
        created_at=str(node.props.get("created_at", "")),
        approved=_approved(graph, proposal_id),
    )


def _approved(graph: GraphStore, proposal_id: str) -> bool:
    return graph.get_node("FlagResolution", _resolution_key(proposal_id)) is not None


def _resolution_key(proposal_id: str) -> str:
    # Mirrors agents/supervisor/store.py: resolution:{flag:<subject_ref>:<severity>}.
    return f"resolution:flag:proposal:{proposal_id}:info"
