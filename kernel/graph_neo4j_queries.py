"""Neo4j GraphStore query runner helpers.

Agent: kernel
Role: execute Neo4j graph queries and convert records into graph value objects.
External I/O: Neo4j database via the owning store's driver.
"""

from __future__ import annotations

from collections.abc import Mapping  # noqa: TC003 - runtime annotations.
from typing import TYPE_CHECKING, Any, cast

from kernel.graph_cypher import (
    _identifier,
    _list_nodes_query,
    _match_node_query,
    _node_from_props,
    _relationship_pattern,
    _set_node_props_query,
    _traverse_query,
)

if TYPE_CHECKING:
    from kernel.graph import Node


class Neo4jGraphQueries:
    """Small query-runner mixin for ``Neo4jGraphStore``."""

    _driver: Any
    _database: str

    def _match_node(self, label_id: str, key: str) -> Mapping[str, Any] | None:
        record = self._one_or_none(_match_node_query(label_id), key=key)
        return None if record is None else record["props"]

    def _list_nodes(self, label: str, label_id: str) -> tuple[Node, ...]:
        records = self._run(_list_nodes_query(label_id))
        return tuple(
            _node_from_props(label, str(record["key"]), record["props"])
            for record in records
        )

    def _set_node_props(
        self, label_id: str, key: str, props: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        record = self._one(
            _set_node_props_query(label_id),
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
        records = self._run(
            _traverse_query(_identifier(node.label), rel, upstream=upstream),
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
        records, _, _ = self._driver.execute_query(
            query, database_=self._database, **params
        )
        return list(records)
