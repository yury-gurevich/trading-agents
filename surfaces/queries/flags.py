"""Human-review flag read model.

Agent: surfaces
Role: project pending Flag nodes for operator surfaces.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from surfaces.queries._graph import nodes_by_label

if TYPE_CHECKING:
    from kernel import GraphStore, Node


@dataclass(frozen=True)
class FlagView:
    """Operator-facing view of one unresolved human-review flag."""

    subject_ref: str
    severity: str
    created_at: str


def pending_flags(graph: GraphStore) -> tuple[FlagView, ...]:
    """Return Flag nodes that have no matching FlagResolution."""
    resolved = {_flag_ref(node) for node in nodes_by_label(graph, "FlagResolution")}
    flags = (
        _view(node)
        for node in nodes_by_label(graph, "Flag")
        if _flag_ref(node) not in resolved
    )
    return tuple(sorted(flags, key=lambda item: (item.severity, item.subject_ref)))


def _view(node: Node) -> FlagView:
    return FlagView(
        subject_ref=str(node.props.get("subject_ref", "")),
        severity=str(node.props.get("severity", "")),
        created_at=str(node.props.get("created_at", "")),
    )


def _flag_ref(node: Node) -> tuple[str, str]:
    return (str(node.props.get("subject_ref", "")), str(node.props.get("severity", "")))
