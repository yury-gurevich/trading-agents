"""In-memory GraphStore backend.

Agent: kernel
Role: provide deterministic append-only graph storage for tests and local probes.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from kernel.errors import CollectingFaultSink, FaultSink, fault_boundary
from kernel.graph import Edge, Node
from kernel.graph_support import (
    NodeKey,
    Props,
    _append_props,
    _edge_allowed,
    _edge_key,
    _node_key,
)

if TYPE_CHECKING:
    from collections.abc import Iterator


class InMemoryGraphStore:
    """Dict-backed GraphStore backend for deterministic tests and local probes."""

    def __init__(self, sink: FaultSink | None = None) -> None:
        """Create an empty in-memory graph with an optional fault sink."""
        self.sink = sink if sink is not None else CollectingFaultSink()
        self._nodes: dict[NodeKey, Node] = {}
        self._edges: list[Edge] = []

    def merge_node(
        self, label: str, key: str, props: Props, *, schema_version: int = 1
    ) -> Node:
        """Create or idempotently merge one node by ``(label, key)``."""
        with fault_boundary(
            self.sink, agent="kernel", module="kernel.graph", reraise=True
        ):
            return self._merge_node(label, key, props, schema_version=schema_version)

    def add_edge(
        self, parent: Node, child: Node, edge_type: str, props: Props | None = None
    ) -> None:
        """Add a directed edge between existing nodes."""
        with fault_boundary(
            self.sink, agent="kernel", module="kernel.graph", reraise=True
        ):
            self._require_node(parent)
            self._require_node(child)
            edge = Edge(_node_key(parent), _node_key(child), edge_type, props or {})
            if all(_edge_key(current) != _edge_key(edge) for current in self._edges):
                self._edges.append(edge)

    def get_node(self, label: str, key: str) -> Node | None:
        """Return a node by ``(label, key)`` if present."""
        with fault_boundary(
            self.sink, agent="kernel", module="kernel.graph", reraise=True
        ):
            return self._nodes.get((label, key))

    def list_nodes(self, label: str) -> tuple[Node, ...]:
        """Return all nodes with the given label."""
        with fault_boundary(
            self.sink, agent="kernel", module="kernel.graph", reraise=True
        ):
            return tuple(node for node in self._nodes.values() if node.label == label)

    def ancestors(
        self, node: Node, *, max_depth: int, edge_types: set[str] | None = None
    ) -> Iterator[Node]:
        """Walk upstream parent nodes."""
        with fault_boundary(
            self.sink, agent="kernel", module="kernel.graph", reraise=True
        ):
            return iter(self._walk(node, max_depth=max_depth, edge_types=edge_types))

    def descendants(
        self, node: Node, *, max_depth: int, edge_types: set[str] | None = None
    ) -> Iterator[Node]:
        """Walk downstream child nodes."""
        with fault_boundary(
            self.sink, agent="kernel", module="kernel.graph", reraise=True
        ):
            return iter(
                self._walk(
                    node, max_depth=max_depth, edge_types=edge_types, downstream=True
                )
            )

    def _merge_node(
        self, label: str, key: str, props: Props, *, schema_version: int
    ) -> Node:
        if schema_version < 1:
            raise ValueError("schema_version must be positive")
        node_key = (label, key)
        current = self._nodes.get(node_key)
        if current is None:
            node = Node(label, key, props, schema_version)
        else:
            if current.schema_version != schema_version:
                raise ValueError("schema_version cannot change for an existing node")
            merged = _append_props(current.props, props)
            node = Node(label, key, merged, schema_version)
        self._nodes[node_key] = node
        return node

    def _require_node(self, node: Node) -> None:
        if _node_key(node) not in self._nodes:
            raise KeyError(f"missing graph node {node.label}.{node.key}")

    def _walk(
        self,
        node: Node,
        *,
        max_depth: int,
        edge_types: set[str] | None,
        downstream: bool = False,
    ) -> list[Node]:
        if max_depth < 1:
            return []
        seen = {_node_key(node)}
        frontier = [_node_key(node)]
        out: list[Node] = []
        for _ in range(max_depth):
            next_frontier: list[NodeKey] = []
            for edge in self._edges:
                source, target = (
                    (edge.parent, edge.child)
                    if downstream
                    else (edge.child, edge.parent)
                )
                if source in frontier and _edge_allowed(edge, edge_types):
                    found = self._nodes[target]
                    if target not in seen:
                        seen.add(target)
                        next_frontier.append(target)
                        out.append(found)
            frontier = next_frontier
            if not frontier:
                break
        return out
