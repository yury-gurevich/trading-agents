"""Graph read helpers for surface projections.

Agent: surfaces
Role: collect label-scoped nodes from graph stores that expose local state.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel import GraphStore, Node


def nodes_by_label(graph: GraphStore, label: str) -> tuple[Node, ...]:
    """Return locally visible nodes for one label."""
    return graph.list_nodes(label)
