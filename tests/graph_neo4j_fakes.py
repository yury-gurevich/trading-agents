"""Fake Neo4j driver helpers for graph backend tests.

Agent: kernel
Role: provide an in-memory Neo4j-driver shape for store and parity tests.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from kernel import GraphSettings, Neo4jGraphStore

if TYPE_CHECKING:
    import pytest


class FakeNeo4jDriver:
    def __init__(self) -> None:
        self.nodes: dict[str, tuple[str, dict[str, object]]] = {}
        self.edges: list[tuple[str, str, str, dict[str, object]]] = []
        self.constraints: list[str] = []
        self.closed = False

    def execute_query(
        self, query: str, **params: object
    ) -> tuple[list[dict[str, object]], None, None]:
        key = str(params.get("key", ""))
        if query.startswith("CREATE CONSTRAINT"):
            self.constraints.append(query)
            return [], None, None
        if "RETURN n.key AS key" in query:
            return self._list_records(query), None, None
        if query.startswith("MATCH (n:") and "SET n +=" not in query:
            return self._node_record(key), None, None
        if query.startswith("MATCH (n:") and "SET n +=" in query:
            self.nodes[key][1].update(dict(params["props"]))  # type: ignore[arg-type]
            return self._node_record(key), None, None
        if query.startswith("MERGE (n:"):
            label = query.split("MERGE (n:`", 1)[1].split("`", 1)[0]
            self.nodes[key] = (label, dict(params["props"]))  # type: ignore[arg-type]
            return self._node_record(key), None, None
        if "MERGE (p)-" in query:
            return self._edge_record(query, params)
        if "RETURN DISTINCT labels(n)" in query:
            return self._traversal_records(query, key)
        msg = f"unexpected query: {query}"
        raise AssertionError(msg)

    def close(self) -> None:
        self.closed = True

    def _node_record(self, key: str) -> list[dict[str, object]]:
        if key not in self.nodes:
            return []
        return [{"props": self.nodes[key][1]}]

    def _list_records(self, query: str) -> list[dict[str, object]]:
        label = query.split("MATCH (n:`", 1)[1].split("`", 1)[0]
        return [
            {"key": key, "props": props}
            for key, (node_label, props) in sorted(self.nodes.items())
            if node_label == label
        ]

    def _edge_record(
        self, query: str, params: dict[str, object]
    ) -> tuple[list[dict[str, object]], None, None]:
        parent_key = str(params["parent_key"])
        child_key = str(params["child_key"])
        if parent_key not in self.nodes or child_key not in self.nodes:
            return [], None, None
        edge_type = query.split("MERGE (p)-[r:`", 1)[1].split("`", 1)[0]
        for parent, child, current_type, props in self.edges:
            if (parent, child, current_type) == (parent_key, child_key, edge_type):
                return [{"props": props}], None, None
        props = dict(params["props"])  # type: ignore[arg-type]
        self.edges.append((parent_key, child_key, edge_type, props))
        return [{"props": props}], None, None

    def _traversal_records(
        self, query: str, key: str
    ) -> tuple[list[dict[str, object]], None, None]:
        upstream = "<-" in query
        out: list[dict[str, object]] = []
        for parent_key, child_key, _edge_type, _props in self.edges:
            wanted = parent_key if upstream and child_key == key else child_key
            if not upstream and parent_key != key:
                continue
            if upstream and child_key != key:
                continue
            label, props = self.nodes[wanted]
            out.append({"labels": [label], "key": wanted, "props": props})
        return out, None, None


def store(monkeypatch: pytest.MonkeyPatch) -> tuple[Neo4jGraphStore, FakeNeo4jDriver]:
    import kernel.graph_neo4j as graph_neo4j

    fake_driver = FakeNeo4jDriver()
    monkeypatch.setattr(
        graph_neo4j.GraphDatabase, "driver", lambda *_args, **_kwargs: fake_driver
    )
    graph = Neo4jGraphStore(
        GraphSettings(
            neo4j_uri="bolt://fake:7687",
            neo4j_user="neo4j",
            neo4j_password="",
        )
    )
    return graph, fake_driver
