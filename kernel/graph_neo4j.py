"""Neo4j-backed GraphStore implementation.

Agent: kernel
Role: adapt generic graph node/edge operations to the Neo4j driver.
External I/O: Neo4j database.
"""

from __future__ import annotations

from collections.abc import Iterator  # noqa: TC003 - runtime annotations.
from typing import Any

from neo4j import GraphDatabase

from kernel.errors import CollectingFaultSink, FaultSink, fault_boundary
from kernel.graph import GraphStore, Node
from kernel.graph_cypher import (
    _add_edge_query,
    _constraint_name,
    _constraint_query,
    _identifier,
    _merge_node_query,
    _new_props,
    _node_from_props,
    _stored_props,
)
from kernel.graph_neo4j_config import GraphSettings
from kernel.graph_neo4j_queries import Neo4jGraphQueries
from kernel.graph_support import Props, _encode_props


class Neo4jGraphStore(GraphStore, Neo4jGraphQueries):
    """Thin Neo4j driver adapter for the GraphStore protocol."""

    def __init__(
        self,
        settings: GraphSettings | None = None,
        sink: FaultSink | None = None,
    ) -> None:
        """Create a Neo4j driver from settings and an optional fault sink."""
        self._settings = settings if settings is not None else GraphSettings()
        self.sink = sink if sink is not None else CollectingFaultSink()
        self._constraint_labels: set[str] = set()
        self._database = self._settings.neo4j_database
        auth = (self._settings.neo4j_user, self._settings.neo4j_password)
        self._driver: Any = GraphDatabase.driver(
            self._settings.neo4j_uri,
            auth=auth,
            connection_timeout=self._settings.neo4j_connection_timeout_seconds,
        )

    def close(self) -> None:
        """Close the underlying Neo4j driver."""
        self._driver.close()

    def merge_node(
        self, label: str, key: str, props: Props, *, schema_version: int = 1
    ) -> Node:
        """Create or idempotently merge one node by ``(label, key)``."""
        with fault_boundary(
            self.sink, agent="kernel", module="kernel.graph", reraise=True
        ):
            encoded = _encode_props(props)
            label_id = _identifier(label)
            self._ensure_constraint(label, label_id)
            current = self._match_node(label_id, key)
            if current is not None:
                stored = _stored_props(current)
                if int(current["schema_version"]) != schema_version:
                    raise ValueError(
                        "schema_version cannot change for an existing node"
                    )
                new_props = _new_props(stored, encoded)
                if new_props:
                    current = self._set_node_props(label_id, key, new_props)
                return _node_from_props(label, key, current)
            stored_props = {"key": key, "schema_version": schema_version, **encoded}
            record = self._one(
                _merge_node_query(label_id),
                key=key,
                props=stored_props,
            )
            return _node_from_props(label, key, record["props"])

    def add_edge(
        self, parent: Node, child: Node, edge_type: str, props: Props | None = None
    ) -> None:
        """Add a directed edge between existing nodes."""
        with fault_boundary(
            self.sink, agent="kernel", module="kernel.graph", reraise=True
        ):
            p_label = _identifier(parent.label)
            c_label = _identifier(child.label)
            rel_type = _identifier(edge_type)
            record = self._one_or_none(
                _add_edge_query(p_label, c_label, rel_type),
                parent_key=parent.key,
                child_key=child.key,
                props=dict(props or {}),
            )
            if record is None:
                raise KeyError("edge endpoints must already exist")

    def get_node(self, label: str, key: str) -> Node | None:
        """Return a node by ``(label, key)`` if present."""
        with fault_boundary(
            self.sink, agent="kernel", module="kernel.graph", reraise=True
        ):
            record = self._match_node(_identifier(label), key)
            return None if record is None else _node_from_props(label, key, record)

    def list_nodes(self, label: str) -> tuple[Node, ...]:
        """Return all nodes with the given label."""
        with fault_boundary(
            self.sink, agent="kernel", module="kernel.graph", reraise=True
        ):
            return self._list_nodes(label, _identifier(label))

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

    def _ensure_constraint(self, label: str, label_id: str) -> None:
        if label in self._constraint_labels:
            return
        self._run(_constraint_query(label_id, _constraint_name(label)))
        self._constraint_labels.add(label)
