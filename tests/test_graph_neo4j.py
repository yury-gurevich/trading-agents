"""Neo4jGraphStore tests with a fake driver and optional live integration."""

from __future__ import annotations

import os
import uuid

import pytest

from kernel import GraphSettings, Neo4jGraphStore, Node


class _FakeNeo4jDriver:
    def __init__(self) -> None:
        self.nodes: dict[str, tuple[str, dict[str, object]]] = {}
        self.edges: list[tuple[str, str, str, dict[str, object]]] = []
        self.closed = False

    def execute_query(
        self, query: str, **params: object
    ) -> tuple[list[dict[str, object]], None, None]:
        key = str(params.get("key", ""))
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
            return self._edge_record(params)
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

    def _edge_record(
        self, params: dict[str, object]
    ) -> tuple[list[dict[str, object]], None, None]:
        parent_key = str(params["parent_key"])
        child_key = str(params["child_key"])
        if parent_key not in self.nodes or child_key not in self.nodes:
            return [], None, None
        props = dict(params["props"])  # type: ignore[arg-type]
        self.edges.append((parent_key, child_key, "DERIVED", props))
        return [{"props": props}], None, None

    def _traversal_records(
        self, query: str, key: str
    ) -> tuple[list[dict[str, object]], None, None]:
        upstream = "<-" in query
        out: list[dict[str, object]] = []
        for parent_key, child_key, _edge_type, _props in self.edges:
            if upstream:
                if child_key != key:
                    continue
                wanted = parent_key
            else:
                if parent_key != key:
                    continue
                wanted = child_key
            label, props = self.nodes[wanted]
            out.append({"labels": [label], "key": wanted, "props": props})
        return out, None, None


def _store(monkeypatch: pytest.MonkeyPatch) -> tuple[Neo4jGraphStore, _FakeNeo4jDriver]:
    import kernel.graph_neo4j as graph_neo4j

    fake_driver = _FakeNeo4jDriver()
    monkeypatch.setattr(
        graph_neo4j.GraphDatabase, "driver", lambda *_args, **_kwargs: fake_driver
    )
    store = Neo4jGraphStore(
        GraphSettings(
            neo4j_uri="bolt://fake:7687",
            neo4j_user="neo4j",
            neo4j_password="",
        )
    )
    return store, fake_driver


def test_neo4j_store_uses_driver_shape_with_fake_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, fake_driver = _store(monkeypatch)

    parent = store.merge_node("Artifact", "parent", {"status": "new"})
    updated = store.merge_node("Artifact", "parent", {"status": "new", "score": 2})
    child = store.merge_node("Artifact", "child", {})
    store.add_edge(updated, child, "DERIVED", {"run": "unit"})

    assert dict(updated.props) == {"status": "new", "score": 2}
    assert store.get_node("Artifact", "parent") == updated
    assert [node.key for node in store.ancestors(child, max_depth=1)] == ["parent"]
    assert [node.key for node in store.descendants(parent, max_depth=1)] == ["child"]
    assert [
        node.key
        for node in store.descendants(parent, max_depth=1, edge_types={"DERIVED"})
    ] == ["child"]
    assert list(store.ancestors(child, max_depth=0)) == []
    with pytest.raises(ValueError, match="schema_version"):
        store.merge_node("Artifact", "parent", {"status": "new"}, schema_version=2)
    store.close()
    assert fake_driver.closed


def test_neo4j_store_records_faults_from_driver_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, _fake_driver = _store(monkeypatch)
    parent = store.merge_node("Artifact", "parent", {})

    with pytest.raises(KeyError):
        store.add_edge(parent, Node("Artifact", "missing"), "DERIVED")
    assert len(store.sink.faults) == 1
    assert store.sink.faults[0].source_module == "kernel.graph"


def test_neo4j_store_raises_when_expected_record_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, _fake_driver = _store(monkeypatch)

    with pytest.raises(LookupError, match="no records"):
        store._one("MATCH (n:`Artifact` {key: $key}) RETURN properties(n) AS props")


def test_neo4j_store_rejects_unsafe_dynamic_identifiers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, _fake_driver = _store(monkeypatch)

    with pytest.raises(ValueError, match="unsafe graph identifier"):
        store.merge_node("Bad Label", "x", {})
    assert len(store.sink.faults) == 1


@pytest.mark.integration
def test_neo4j_graph_store_round_trip_when_configured() -> None:
    uri = os.getenv("NEO4J_TEST_URI")
    if not uri:
        pytest.skip("NEO4J_TEST_URI is not set")

    from neo4j import GraphDatabase

    user = os.getenv("NEO4J_TEST_USER", os.getenv("NEO4J_USER", "neo4j"))
    password = os.getenv("NEO4J_TEST_PASSWORD", os.getenv("NEO4J_PASSWORD", ""))
    suffix = uuid.uuid4().hex
    parent_key = f"parent-{suffix}"
    child_key = f"child-{suffix}"
    settings = GraphSettings(
        neo4j_uri=uri,
        neo4j_user=user,
        neo4j_password=password,
    )
    store = Neo4jGraphStore(settings)
    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        parent = store.merge_node("GraphStoreTest", parent_key, {"run": suffix})
        child = store.merge_node("GraphStoreTest", child_key, {"run": suffix})
        store.add_edge(parent, child, "DERIVED", {"run": suffix})

        assert store.get_node("GraphStoreTest", parent_key) == parent
        assert [node.key for node in store.ancestors(child, max_depth=1)] == [
            parent_key
        ]
    finally:
        driver.execute_query(
            "MATCH (n:GraphStoreTest) WHERE n.key IN $keys DETACH DELETE n",
            keys=[parent_key, child_key],
        )
        driver.close()
        store.close()
