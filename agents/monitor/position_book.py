"""Current Position-node view for monitor decisions.

Agent: monitor
Role: filter graph Position nodes down to the active broker-aware book.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.positions import active_position_nodes

if TYPE_CHECKING:
    from kernel import GraphStore, Node


def active_positions(graph: GraphStore) -> tuple[Node, ...]:
    """Return open Position nodes not superseded by broker reconciliation."""
    return active_position_nodes(graph)
