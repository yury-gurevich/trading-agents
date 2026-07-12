"""PostgreSQL-backed GraphStore implementation.

Agent: kernel
Role: adapt generic graph node/edge operations to psycopg and the PG spine schema.
External I/O: PostgreSQL database.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping  # noqa: TC003 - runtime.
from typing import Any, cast

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from kernel.errors import CollectingFaultSink, FaultSink, fault_boundary
from kernel.graph import GraphStore, Node
from kernel.graph_postgres_config import PostgresGraphSettings
from kernel.graph_postgres_queries import (
    ADD_EDGE_SQL,
    GET_NODE_SQL,
    LIST_NODES_SQL,
    MERGE_NODE_SQL,
    NODE_EXISTS_SQL,
    TRAVERSE_ANCESTORS_SQL,
    TRAVERSE_DESCENDANTS_SQL,
    json_props,
    node_from_row,
)
from kernel.graph_support import Props, _append_props


class PostgresGraphStore(GraphStore):
    """Thin psycopg adapter for the GraphStore protocol."""

    def __init__(
        self,
        settings: PostgresGraphSettings | None = None,
        sink: FaultSink | None = None,
        connection: Any | None = None,  # noqa: ANN401 - tests inject a fake DB-API shape.
    ) -> None:
        """Create a PostgreSQL connection from settings or use an injected one."""
        self._settings = settings if settings is not None else PostgresGraphSettings()
        self.sink = sink if sink is not None else CollectingFaultSink()
        self._owns_conn = connection is None
        self._conn: Any = connection if connection is not None else self._connect()

    def close(self) -> None:
        """Close the underlying PostgreSQL connection."""
        self._conn.close()

    def merge_node(
        self, label: str, key: str, props: Props, *, schema_version: int = 1
    ) -> Node:
        """Create or idempotently merge one node by ``(label, key)``."""
        with fault_boundary(
            self.sink, agent="kernel", module="kernel.graph", reraise=True
        ):
            if schema_version < 1:
                raise ValueError("schema_version must be positive")
            row = self._fetchone(
                MERGE_NODE_SQL,
                (label, key, Jsonb(json_props(props)), schema_version),
            )
            if row is not None:
                return node_from_row(row)
            return self._raise_merge_conflict(label, key, props, schema_version)

    def add_edge(
        self, parent: Node, child: Node, edge_type: str, props: Props | None = None
    ) -> None:
        """Add a directed edge between existing nodes."""
        with fault_boundary(
            self.sink, agent="kernel", module="kernel.graph", reraise=True
        ):
            self._require_node(parent)
            self._require_node(child)
            self._execute(
                ADD_EDGE_SQL,
                (
                    parent.label,
                    parent.key,
                    child.label,
                    child.key,
                    edge_type,
                    Jsonb(json_props(props or {})),
                ),
            )

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

    def _connect(self) -> Any:  # noqa: ANN401 - psycopg connection shape is sufficient.
        return psycopg.connect(
            self._settings.postgres_dsn,
            autocommit=True,
            connect_timeout=int(self._settings.postgres_connect_timeout_seconds),
            row_factory=dict_row,
        )

    def _raise_merge_conflict(
        self, label: str, key: str, props: Props, schema_version: int
    ) -> Node:
        current = self.get_node(label, key)
        if current is None:
            raise LookupError("PostgreSQL node merge returned no rows")
        if current.schema_version != schema_version:
            raise ValueError("schema_version cannot change for an existing node")
        _append_props(current.props, props)
        raise LookupError("PostgreSQL node merge returned no rows")

    def _require_node(self, node: Node) -> None:
        if self._fetchone(NODE_EXISTS_SQL, (node.label, node.key)) is None:
            raise KeyError(f"missing graph node {node.label}.{node.key}")

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

    def _fetchone(
        self, query: str, params: tuple[object, ...]
    ) -> Mapping[str, Any] | None:
        return cast(
            "Mapping[str, Any] | None",
            self._run(query, params, lambda cursor: cursor.fetchone()),
        )

    def _fetchall(
        self, query: str, params: tuple[object, ...]
    ) -> list[Mapping[str, Any]]:
        return list(self._run(query, params, lambda cursor: cursor.fetchall()))

    def _execute(self, query: str, params: tuple[object, ...]) -> None:
        self._run(query, params, lambda _cursor: None)

    def _run(
        self,
        query: str,
        params: tuple[object, ...],
        collect: Callable[[Any], Any],
    ) -> Any:  # noqa: ANN401 - returns whatever the collect callback yields.
        # Single autocommit statements, so one retry on a server-dropped
        # connection (Neon idles out long-lived surfaces) is safe; injected
        # test connections are never replaced.
        try:
            with self._conn.cursor() as cursor:
                cursor.execute(query, params)
                return collect(cursor)
        except psycopg.OperationalError:
            if not self._owns_conn:
                raise
            self._conn = self._connect()
            with self._conn.cursor() as cursor:
                cursor.execute(query, params)
                return collect(cursor)
