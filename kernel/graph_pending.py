"""Pending-work lookup for graph-pull polls (DL-246).

Agent: kernel
Role: find the nodes of a label that lack a processed edge by key and edge alone,
      then fetch props only for those, in the store's list order.
External I/O: GraphStore reads via the injected backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from kernel.graph import GraphStore, Node


def pending_nodes(
    graph: GraphStore,
    label: str,
    edge_type: str,
    *,
    created_at_from: datetime | None = None,
) -> list[Node]:
    """``label`` nodes with no outgoing ``edge_type`` edge, fetched one by one.

    A poll that finds no work downloads no props; one that finds work downloads
    exactly that work. A key that vanished between the query and the fetch is
    skipped (the graph is append-only, so this is a race, not a state).
    """
    keys = graph.keys_without_edge(label, edge_type, created_at_from=created_at_from)
    nodes = (graph.get_node(label, key) for key in keys)
    return [node for node in nodes if node is not None]
