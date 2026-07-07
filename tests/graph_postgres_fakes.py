"""Fake psycopg connection helpers for graph backend tests.

Agent: kernel
Role: provide an in-memory psycopg shape for PostgresGraphStore parity tests.
External I/O: none.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from kernel.graph_postgres import PostgresGraphStore
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
)
from kernel.graph_support import NodeKey, _append_props

if TYPE_CHECKING:
    import pytest

type Row = dict[str, object]
type StorePair = tuple[PostgresGraphStore, FakePostgresConnection]


class FakePostgresConnection:
    def __init__(self) -> None:
        self.nodes: dict[NodeKey, Row] = {}
        self.edges: list[tuple[NodeKey, NodeKey, str, dict[str, object]]] = []
        self.closed = False
        self.drop_next_merge = False
        self.connect_args: tuple[tuple[object, ...], dict[str, object]] | None = None

    def cursor(self) -> FakePostgresCursor:
        return FakePostgresCursor(self)

    def close(self) -> None:
        self.closed = True


class FakePostgresCursor:
    def __init__(self, connection: FakePostgresConnection) -> None:
        self.connection = connection
        self.result: list[Row] = []

    def __enter__(self) -> FakePostgresCursor:
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def execute(self, query: str, params: tuple[object, ...]) -> None:
        if query == MERGE_NODE_SQL:
            self.result = self._merge_node(params)
        elif query == GET_NODE_SQL:
            self.result = self._node_record(str(params[0]), str(params[1]))
        elif query == LIST_NODES_SQL:
            self.result = self._list_nodes(str(params[0]))
        elif query == NODE_EXISTS_SQL:
            self.result = self._exists(str(params[0]), str(params[1]))
        elif query == ADD_EDGE_SQL:
            self.result = self._add_edge(params)
        elif query in (TRAVERSE_ANCESTORS_SQL, TRAVERSE_DESCENDANTS_SQL):
            self.result = self._traverse(query, params)
        else:
            raise AssertionError(f"unexpected query: {query}")

    def fetchone(self) -> Mapping[str, object] | None:
        return self.result[0] if self.result else None

    def fetchall(self) -> list[Mapping[str, object]]:
        return list(self.result)

    def _merge_node(self, params: tuple[object, ...]) -> list[Row]:
        label, key = str(params[0]), str(params[1])
        raw_props, schema_version = _json(params[2]), int(params[3])
        if self.connection.drop_next_merge:
            self.connection.drop_next_merge = False
            return []
        node_key = (label, key)
        current = self.connection.nodes.get(node_key)
        if current is None:
            row = _row(label, key, raw_props, schema_version)
            self.connection.nodes[node_key] = row
            return [row]
        if int(current["schema_version"]) != schema_version:
            return []
        try:
            props = json_props(_append_props(current["props"], raw_props))
        except ValueError:
            return []
        row = _row(label, key, props, schema_version)
        self.connection.nodes[node_key] = row
        return [row]

    def _node_record(self, label: str, key: str) -> list[Row]:
        row = self.connection.nodes.get((label, key))
        return [] if row is None else [row]

    def _list_nodes(self, label: str) -> list[Row]:
        return [
            row
            for (node_label, _key), row in sorted(self.connection.nodes.items())
            if node_label == label
        ]

    def _exists(self, label: str, key: str) -> list[Row]:
        return [{"exists": 1}] if (label, key) in self.connection.nodes else []

    def _add_edge(self, params: tuple[object, ...]) -> list[Row]:
        parent = (str(params[0]), str(params[1]))
        child = (str(params[2]), str(params[3]))
        edge_type = str(params[4])
        props = dict(_json(params[5]))
        if not any(
            (parent, child, edge_type) == (p, c, current_type)
            for p, c, current_type, _props in self.connection.edges
        ):
            self.connection.edges.append((parent, child, edge_type, props))
        return []

    def _traverse(self, query: str, params: tuple[object, ...]) -> list[Row]:
        upstream = query == TRAVERSE_ANCESTORS_SQL
        filters = None if params[2] is None else set(params[2])
        max_depth = int(params[4])
        seen = {(str(params[0]), str(params[1]))}
        frontier = list(seen)
        out: list[Row] = []
        for _depth in range(max_depth):
            found = self._next_frontier(frontier, filters, upstream)
            frontier = []
            for key in sorted(dict.fromkeys(found), key=lambda item: item[1]):
                if key in seen:
                    continue
                seen.add(key)
                frontier.append(key)
                out.append(self.connection.nodes[key])
            if not frontier:
                break
        return out

    def _next_frontier(
        self, frontier: list[NodeKey], filters: set[object] | None, upstream: bool
    ) -> list[NodeKey]:
        found: list[NodeKey] = []
        for parent, child, edge_type, _props in self.connection.edges:
            if filters is not None and edge_type not in filters:
                continue
            source, target = (child, parent) if upstream else (parent, child)
            if source in frontier:
                found.append(target)
        return found


def store(monkeypatch: pytest.MonkeyPatch) -> StorePair:
    import kernel.graph_postgres as graph_postgres

    fake = FakePostgresConnection()
    monkeypatch.setattr(graph_postgres, "Jsonb", lambda value: value)
    graph = PostgresGraphStore(
        PostgresGraphSettings(postgres_dsn="postgresql://fake/db"),
        connection=fake,
    )
    return graph, fake


def connectable(monkeypatch: pytest.MonkeyPatch) -> FakePostgresConnection:
    import kernel.graph_postgres as graph_postgres

    fake = FakePostgresConnection()

    def connect(*args: object, **kwargs: object) -> FakePostgresConnection:
        fake.connect_args = (args, kwargs)
        return fake

    monkeypatch.setattr(graph_postgres.psycopg, "connect", connect)
    return fake


def _row(label: str, key: str, props: Mapping[str, Any], schema_version: int) -> Row:
    return {
        "label": label,
        "key": key,
        "props": dict(props),
        "schema_version": schema_version,
    }


def _json(value: object) -> Mapping[str, Any]:
    obj = value if isinstance(value, Mapping) else getattr(value, "obj", value)
    return obj if isinstance(obj, Mapping) else {}
