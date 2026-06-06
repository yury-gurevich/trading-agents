"""Neo4j-backed GraphStore implementation.

Agent: kernel
Role: adapt generic graph node/edge operations to the Neo4j driver.
External I/O: Neo4j database.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping  # noqa: TC003 - runtime annotations.
from typing import Any, cast

from neo4j import GraphDatabase

from kernel.config import AgentSettings, tunable
from kernel.errors import CollectingFaultSink, FaultSink, fault_boundary
from kernel.graph import GraphStore, Node
from kernel.graph_cypher import (
    _identifier,
    _new_props,
    _node_from_props,
    _relationship_pattern,
    _stored_props,
)
from kernel.graph_support import Props  # noqa: TC001 - public store signatures.


class GraphSettings(AgentSettings):
    """Infrastructure settings for the Neo4j graph store."""

    neo4j_uri: str = tunable(
        "bolt://localhost:7687", why="Default local Neo4j graph endpoint."
    )
    neo4j_user: str = tunable(
        "neo4j", why="Conventional local bootstrap user keeps setup predictable."
    )
    neo4j_password: str = tunable(
        "", why="Provided out-of-band; empty supports unauthenticated tests."
    )
    neo4j_connection_timeout_seconds: float = tunable(
        30.0,
        why="Fail a broken graph connection promptly while allowing local startup lag.",
        ge=1.0,
        le=120.0,
        unit="seconds",
    )


class Neo4jGraphStore(GraphStore):
    """Thin Neo4j driver adapter for the GraphStore protocol."""

    def __init__(
        self,
        settings: GraphSettings | None = None,
        sink: FaultSink | None = None,
    ) -> None:
        """Create a Neo4j driver from settings and an optional fault sink."""
        self._settings = settings if settings is not None else GraphSettings()
        self.sink = sink if sink is not None else CollectingFaultSink()
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
            label_id = _identifier(label)
            current = self._match_node(label_id, key)
            if current is not None:
                stored = _stored_props(current)
                if int(current["schema_version"]) != schema_version:
                    raise ValueError(
                        "schema_version cannot change for an existing node"
                    )
                new_props = _new_props(stored, props)
                if new_props:
                    current = self._set_node_props(label_id, key, new_props)
                return _node_from_props(label, key, current)
            stored_props = {"key": key, "schema_version": schema_version, **dict(props)}
            record = self._one(
                f"MERGE (n:{label_id} {{key: $key}}) "
                "ON CREATE SET n += $props "
                "RETURN properties(n) AS props",
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
                f"MATCH (p:{p_label} {{key: $parent_key}}), "
                f"(c:{c_label} {{key: $child_key}}) "
                f"MERGE (p)-[r:{rel_type}]->(c) "
                "ON CREATE SET r += $props "
                "RETURN properties(r) AS props",
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

    def _match_node(self, label_id: str, key: str) -> Mapping[str, Any] | None:
        record = self._one_or_none(
            f"MATCH (n:{label_id} {{key: $key}}) RETURN properties(n) AS props",
            key=key,
        )
        return None if record is None else record["props"]

    def _set_node_props(
        self, label_id: str, key: str, props: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        record = self._one(
            f"MATCH (n:{label_id} {{key: $key}}) "
            "SET n += $props RETURN properties(n) AS props",
            key=key,
            props=dict(props),
        )
        return cast("Mapping[str, Any]", record["props"])

    def _traverse(
        self, node: Node, max_depth: int, edge_types: set[str] | None, *, upstream: bool
    ) -> list[Node]:
        if max_depth < 1:
            return []
        rel = _relationship_pattern(edge_types, max_depth)
        direction = f"<-{rel}-" if upstream else f"-{rel}->"
        records = self._run(
            f"MATCH (start:{_identifier(node.label)} {{key: $key}}){direction}(n) "
            "RETURN DISTINCT labels(n) AS labels, n.key AS key, properties(n) AS props",
            key=node.key,
        )
        return [
            _node_from_props(
                str(record["labels"][0]), str(record["key"]), record["props"]
            )
            for record in records
        ]

    def _one(self, query: str, **params: object) -> Any:  # noqa: ANN401 - Neo4j Record
        record = self._one_or_none(query, **params)
        if record is None:
            raise LookupError("Neo4j query returned no records")
        return record

    def _one_or_none(self, query: str, **params: object) -> Any | None:  # noqa: ANN401 - Neo4j Record
        records = self._run(query, **params)
        return records[0] if records else None

    def _run(self, query: str, **params: object) -> list[Any]:
        records, _, _ = self._driver.execute_query(query, **params)
        return list(records)
