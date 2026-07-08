"""Current Position-node view for monitor decisions.

Agent: monitor
Role: filter graph Position nodes down to the active broker-aware book.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.monitor.store import is_open_position

if TYPE_CHECKING:
    from kernel import GraphStore, Node


def active_positions(graph: GraphStore) -> tuple[Node, ...]:
    """Return open Position nodes not superseded by broker reconciliation."""
    return tuple(
        node
        for node in graph.list_nodes("Position")
        if _broker_active(node) and is_open_position(graph, node)
    )


def _broker_active(node: Node) -> bool:
    if node.props.get("status", "open") != "open":
        return False
    return not (
        node.props.get("broker_absent") or node.props.get("broker_superseded_by")
    )
