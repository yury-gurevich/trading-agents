"""Neo4jGraphStore tests with a fake driver and optional live integration."""

from __future__ import annotations

import os
import uuid

import pytest
from tests.graph_neo4j_fakes import store as fake_store

from kernel import GraphSettings, Neo4jGraphStore, Node


def test_neo4j_store_uses_driver_shape_with_fake_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, fake_driver = fake_store(monkeypatch)

    parent = store.merge_node("Artifact", "parent", {"status": "new"})
    replayed = store.merge_node("Artifact", "parent", {"status": "new"})
    updated = store.merge_node("Artifact", "parent", {"status": "new", "score": 2})
    child = store.merge_node("Artifact", "child", {})
    store.add_edge(updated, child, "DERIVED", {"run": "unit"})

    assert replayed == parent
    assert dict(updated.props) == {"status": "new", "score": 2}
    assert store.get_node("Artifact", "parent") == updated
    assert store.list_nodes("Artifact") == (child, updated)
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
    store, _fake_driver = fake_store(monkeypatch)
    parent = store.merge_node("Artifact", "parent", {})

    with pytest.raises(KeyError):
        store.add_edge(parent, Node("Artifact", "missing"), "DERIVED")
    assert len(store.sink.faults) == 1
    assert store.sink.faults[0].source_module == "kernel.graph"


def test_neo4j_store_raises_when_expected_record_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, _fake_driver = fake_store(monkeypatch)

    with pytest.raises(LookupError, match="no records"):
        store._one("MATCH (n:`Artifact` {key: $key}) RETURN properties(n) AS props")


def test_neo4j_store_rejects_unsafe_dynamic_identifiers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, _fake_driver = fake_store(monkeypatch)

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
        assert parent in store.list_nodes("GraphStoreTest")
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
