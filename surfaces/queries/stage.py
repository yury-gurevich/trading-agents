"""Stage query projections.

Agent: surfaces
Role: read StageTransition nodes and project stage history views.
External I/O: GraphStore reads.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from surfaces.queries._graph import nodes_by_label

if TYPE_CHECKING:
    from kernel import GraphStore, Node


@dataclass(frozen=True)
class StageView:
    """Operator-facing view of one execution stage transition."""

    from_stage: str
    to_stage: str
    reason: str
    transitioned_at: str


def stage_history(graph: GraphStore) -> tuple[StageView, ...]:
    """Return all StageTransition nodes, oldest first."""
    views = (_view(node) for node in nodes_by_label(graph, "StageTransition"))
    return tuple(sorted(views, key=lambda item: item.transitioned_at))


def current_stage(graph: GraphStore, *, default: str = "paper") -> str:
    """Return the current execution stage, or default if no transition exists."""
    history = stage_history(graph)
    if not history:
        return default
    return history[-1].to_stage


def _view(node: Node) -> StageView:
    return StageView(
        from_stage=str(node.props.get("from_stage", "")),
        to_stage=str(node.props.get("to_stage", "")),
        reason=str(node.props.get("reason", "")),
        transitioned_at=str(node.props.get("transitioned_at", "")),
    )
