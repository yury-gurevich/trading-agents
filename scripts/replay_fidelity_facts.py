"""A read-only graph over one exported S237 session's book facts.

Agent: tooling
Role: serve the export's Position and snapshot facts to the fleet's own graph readers
      as a whole `GraphStore`; refuse the writes and walks an export cannot answer.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, NoReturn

if TYPE_CHECKING:
    from collections.abc import Iterator
    from datetime import datetime

    from kernel.graph import Node
    from kernel.graph_support import Props


class ExportedFacts:
    """A read-only view over the export's book facts, for the fleet's own readers.

    `open_positions` and `portfolio_from_graph` only list nodes by label, so the book
    is served, never merged: its labels belong to execution and the monitor. The
    export carries no edges, so a walk is refused rather than answered empty.
    """

    def __init__(self, nodes: tuple[Node, ...]) -> None:
        """Hold the exported snapshot and Position facts."""
        self._nodes = nodes

    def list_nodes(self, label: str) -> tuple[Node, ...]:
        """Return the exported facts carrying ``label``."""
        return tuple(node for node in self._nodes if node.label == label)

    def get_node(self, label: str, key: str) -> Node | None:
        """Return the exported fact at ``(label, key)``, if the export holds it."""
        return next((node for node in self.list_nodes(label) if node.key == key), None)

    def merge_node(
        self,
        label: str,
        key: str,
        props: Props,  # noqa: ARG002 - port signature; the view is read-only.
        *,
        schema_version: int = 1,  # noqa: ARG002 - port signature; read-only.
    ) -> Node:
        """Refuse: replayed facts are served, never written."""
        _refuse(f"merge_node({label}, {key})")

    def add_edge(
        self,
        parent: Node,
        child: Node,
        edge_type: str,
        props: Props | None = None,  # noqa: ARG002 - port signature; read-only.
    ) -> None:
        """Refuse: replayed facts are served, never written."""
        _refuse(f"add_edge({parent.label} -{edge_type}-> {child.label})")

    def ancestors(
        self,
        node: Node,
        *,
        max_depth: int,  # noqa: ARG002 - port signature; the export has no edges.
        edge_types: set[str] | None = None,  # noqa: ARG002 - port signature.
    ) -> Iterator[Node]:
        """Refuse: the export carries no edges, so no walk can be answered."""
        _refuse(f"ancestors({node.label}, {node.key})")

    def descendants(
        self,
        node: Node,
        *,
        max_depth: int,  # noqa: ARG002 - port signature; the export has no edges.
        edge_types: set[str] | None = None,  # noqa: ARG002 - port signature.
    ) -> Iterator[Node]:
        """Refuse: the export carries no edges, so no walk can be answered."""
        _refuse(f"descendants({node.label}, {node.key})")

    def keys_without_edge(
        self,
        label: str,
        edge_type: str,
        *,
        downstream: bool = True,
        created_at_from: datetime | None = None,
    ) -> tuple[str, ...]:
        """Refuse: with no edges exported, "no such edge" would read as a fact."""
        direction = "out" if downstream else "in"
        _refuse(
            f"keys_without_edge({label}, {edge_type} {direction}, {created_at_from})"
        )


def _refuse(call: str) -> NoReturn:
    message = f"an exported session is a read-only view without edges: {call}"
    raise PermissionError(message)
