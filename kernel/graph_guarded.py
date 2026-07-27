"""GraphStore wrapper that enforces a declared vocabulary on every write.

Agent: kernel
Role: reject a write that does not conform to the declared vocabulary, at the
      moment it is attempted rather than when a later read comes back empty.
External I/O: none — delegates to the wrapped store.

Reads pass through untouched. This only ever says no; it never adds a node, an
edge, or a derived fact (R007).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from kernel.graph import GraphStore, Node
    from kernel.graph_support import Props
    from kernel.graph_vocabulary import Vocabulary


class GuardedGraphStore:
    """Wrap a ``GraphStore`` so every write is checked against a vocabulary."""

    def __init__(
        self, inner: GraphStore, vocabulary: Vocabulary, *, writer: str = ""
    ) -> None:
        """Guard *inner*; *writer* enables the per-agent ownership check."""
        self._inner = inner
        self._vocabulary = vocabulary
        self._writer = writer

    def merge_node(
        self, label: str, key: str, props: Props, *, schema_version: int = 1
    ) -> Node:
        """Check the label, then merge through to the wrapped store."""
        self._vocabulary.check_node(label, writer=self._writer)
        return self._inner.merge_node(label, key, props, schema_version=schema_version)

    def add_edge(
        self, parent: Node, child: Node, edge_type: str, props: Props | None = None
    ) -> None:
        """Check the edge shape, then add it through to the wrapped store."""
        self._vocabulary.check_edge(parent.label, edge_type, child.label)
        self._inner.add_edge(parent, child, edge_type, props)

    def get_node(self, label: str, key: str) -> Node | None:
        """Read through to the wrapped store."""
        return self._inner.get_node(label, key)

    def list_nodes(self, label: str) -> tuple[Node, ...]:
        """Read through to the wrapped store."""
        return self._inner.list_nodes(label)

    def ancestors(
        self, node: Node, *, max_depth: int, edge_types: set[str] | None = None
    ) -> Iterator[Node]:
        """Read through to the wrapped store."""
        return self._inner.ancestors(node, max_depth=max_depth, edge_types=edge_types)

    def descendants(
        self, node: Node, *, max_depth: int, edge_types: set[str] | None = None
    ) -> Iterator[Node]:
        """Read through to the wrapped store."""
        return self._inner.descendants(node, max_depth=max_depth, edge_types=edge_types)
