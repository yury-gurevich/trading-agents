"""Read side of the PostgreSQL-backed GraphStore (split out of graph_postgres, S242).

Agent: kernel
Role: serve the port's read methods - get, list, the key-and-edge query and both
      traversals - over the adapter's single-statement fetch helpers.
External I/O: PostgreSQL database, through the adapter's connection.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from kernel.errors import fault_boundary
from kernel.graph_postgres_keys import (
    KEYS_WITHOUT_INCOMING_SQL,
    KEYS_WITHOUT_OUTGOING_SQL,
)
from kernel.graph_postgres_queries import (
    GET_NODE_SQL,
    LIST_NODES_SQL,
    TRAVERSE_ANCESTORS_SQL,
    TRAVERSE_DESCENDANTS_SQL,
    node_from_row,
)
from kernel.graph_support import created_at_bound

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping
    from datetime import datetime

    from kernel.errors import FaultSink
    from kernel.graph import Node

type _Params = tuple[object, ...]


class PostgresGraphReads:
    """Read methods for ``PostgresGraphStore``; the adapter supplies the fetches."""

    sink: FaultSink
    _fetchone: Callable[[str, _Params], Mapping[str, Any] | None]
    _fetchall: Callable[[str, _Params], list[Mapping[str, Any]]]

    def get_node(self, label: str, key: str) -> Node | None:
        """Return a node by ``(label, key)`` if present."""
        with fault_boundary(
            self.sink, agent="kernel", module="kernel.graph", reraise=True
        ):
            row = self._fetchone(GET_NODE_SQL, (label, key))
            return None if row is None else node_from_row(row)

    def list_nodes(self, label: str) -> tuple[Node, ...]:
        """Return all nodes with the given label."""
        with fault_boundary(
            self.sink, agent="kernel", module="kernel.graph", reraise=True
        ):
            return tuple(
                node_from_row(row) for row in self._fetchall(LIST_NODES_SQL, (label,))
            )

    def keys_without_edge(
        self,
        label: str,
        edge_type: str,
        *,
        downstream: bool = True,
        created_at_from: datetime | None = None,
    ) -> tuple[str, ...]:
        """Return keys of ``label`` nodes with no ``edge_type`` edge: one anti-join."""
        with fault_boundary(
            self.sink, agent="kernel", module="kernel.graph", reraise=True
        ):
            bound = (
                None if created_at_from is None else created_at_bound(created_at_from)
            )
            query = (
                KEYS_WITHOUT_OUTGOING_SQL if downstream else KEYS_WITHOUT_INCOMING_SQL
            )
            rows = self._fetchall(query, (label, edge_type, bound, bound))
            return tuple(str(row["key"]) for row in rows)

    def ancestors(
        self, node: Node, *, max_depth: int, edge_types: set[str] | None = None
    ) -> Iterator[Node]:
        """Walk upstream parent nodes."""
        with fault_boundary(
            self.sink, agent="kernel", module="kernel.graph", reraise=True
        ):
            return iter(self._traverse(node, max_depth, edge_types, upstream=True))

    def descendants(
        self, node: Node, *, max_depth: int, edge_types: set[str] | None = None
    ) -> Iterator[Node]:
        """Walk downstream child nodes."""
        with fault_boundary(
            self.sink, agent="kernel", module="kernel.graph", reraise=True
        ):
            return iter(self._traverse(node, max_depth, edge_types, upstream=False))

    def _traverse(
        self,
        node: Node,
        max_depth: int,
        edge_types: set[str] | None,
        *,
        upstream: bool,
    ) -> list[Node]:
        if max_depth < 1:
            return []
        filters = None if edge_types is None else sorted(edge_types)
        query = TRAVERSE_ANCESTORS_SQL if upstream else TRAVERSE_DESCENDANTS_SQL
        params = (node.label, node.key, filters, filters, max_depth, filters, filters)
        return [node_from_row(row) for row in self._fetchall(query, params)]
