"""GraphStore protocol and value types.

Agent: kernel
Role: define generic append-only graph storage interfaces for provenance storage.
External I/O: none.
"""

from __future__ import annotations

from collections.abc import Iterator  # noqa: TC003 - Protocol evaluated at runtime.
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol

from kernel.graph_support import NodeKey, Props, _frozen_props

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True)
class Node:
    """One append-only graph node, uniquely identified by ``(label, key)``."""

    label: str
    key: str
    props: Props = field(default_factory=dict)
    schema_version: int = 1

    def __post_init__(self) -> None:
        """Freeze top-level props so returned nodes cannot be mutated in place."""
        object.__setattr__(self, "props", _frozen_props(self.props))


@dataclass(frozen=True)
class Edge:
    """One directed relationship between two graph nodes."""

    parent: NodeKey
    child: NodeKey
    edge_type: str
    props: Props = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Freeze top-level props so returned edges cannot be mutated in place."""
        object.__setattr__(self, "props", _frozen_props(self.props))


class GraphStore(Protocol):
    """Minimal append-only graph storage protocol."""

    def merge_node(
        self, label: str, key: str, props: Props, *, schema_version: int = 1
    ) -> Node:
        """Create or idempotently merge one node by ``(label, key)``."""
        ...  # pragma: no cover - protocol declaration only.

    def add_edge(
        self, parent: Node, child: Node, edge_type: str, props: Props | None = None
    ) -> None:
        """Add a directed edge between existing nodes."""
        ...  # pragma: no cover - protocol declaration only.

    def get_node(self, label: str, key: str) -> Node | None:
        """Return a node by ``(label, key)`` if present."""
        ...  # pragma: no cover - protocol declaration only.

    def list_nodes(self, label: str) -> tuple[Node, ...]:
        """Return all nodes with the given label."""
        ...  # pragma: no cover - protocol declaration only.

    def keys_without_edge(
        self,
        label: str,
        edge_type: str,
        *,
        downstream: bool = True,
        created_at_from: datetime | None = None,
    ) -> tuple[str, ...]:
        """Return keys of ``label`` nodes with no ``edge_type`` edge, no props.

        ``downstream`` asks for no outgoing edge (the node is never that edge's
        parent), else no incoming one. ``created_at_from`` keeps only nodes whose
        ``created_at`` string sorts at or after it in UTC. Keys come back in this
        store's ``list_nodes`` order.
        """
        ...  # pragma: no cover - protocol declaration only.

    def ancestors(
        self, node: Node, *, max_depth: int, edge_types: set[str] | None = None
    ) -> Iterator[Node]:
        """Walk upstream parent nodes."""
        ...  # pragma: no cover - protocol declaration only.

    def descendants(
        self, node: Node, *, max_depth: int, edge_types: set[str] | None = None
    ) -> Iterator[Node]:
        """Walk downstream child nodes."""
        ...  # pragma: no cover - protocol declaration only.
