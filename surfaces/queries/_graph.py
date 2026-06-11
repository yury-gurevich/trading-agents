"""Graph read helpers for surface projections.

Agent: surfaces
Role: collect label-scoped nodes from graph stores that expose local state.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from kernel import Node

if TYPE_CHECKING:
    from kernel import GraphStore


def nodes_by_label(graph: GraphStore, label: str) -> tuple[Node, ...]:
    """Return locally visible nodes for one label."""
    raw_nodes = getattr(graph, "_nodes", None)
    if not isinstance(raw_nodes, dict):
        return ()
    return tuple(
        node
        for node in raw_nodes.values()
        if isinstance(node, Node) and node.label == label
    )
