"""GraphStore backend rigor parity tests.

Agent: kernel
Role: verify shared graph semantics across in-memory and Neo4j backends.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.graph_neo4j_fakes import store as fake_neo4j_store
from tests.graph_postgres_fakes import store as fake_postgres_store

from kernel import GraphStore, InMemoryGraphStore
from kernel.graph_support import (
    _decode_props,
    _encode_props,
    _neo4j_native,
    _prim_kind,
)

if TYPE_CHECKING:
    import pytest


def test_edge_identity_matches_between_backends(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    neo4j, fake_driver = fake_neo4j_store(monkeypatch)
    postgres, fake_postgres = fake_postgres_store(monkeypatch)
    memory = InMemoryGraphStore()

    assert _edge_walk(memory) == _edge_walk(neo4j) == _edge_walk(postgres)
    assert len(memory._edges) == 1
    assert len(fake_driver.edges) == 1
    assert fake_driver.edges[0][3] == {"run": "first"}
    assert len(fake_postgres.edges) == 1
    assert fake_postgres.edges[0][3] == {"run": "first"}


def test_neo4j_constraints_are_installed_once_per_label(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph, fake_driver = fake_neo4j_store(monkeypatch)

    graph.merge_node("Artifact", "one", {})
    graph.merge_node("Artifact", "two", {})
    graph.merge_node("OtherArtifact", "one", {})

    assert fake_driver.constraints == [
        "CREATE CONSTRAINT `Artifact_key_unique` IF NOT EXISTS "
        "FOR (n:`Artifact`) REQUIRE n.key IS UNIQUE",
        "CREATE CONSTRAINT `OtherArtifact_key_unique` IF NOT EXISTS "
        "FOR (n:`OtherArtifact`) REQUIRE n.key IS UNIQUE",
    ]


def test_prim_kind_classifies_neo4j_primitives() -> None:
    assert _prim_kind(True) == "bool"
    assert _prim_kind(3) == "int"
    assert _prim_kind(1.5) == "float"
    assert _prim_kind("x") == "str"
    assert _prim_kind(None) is None


def test_neo4j_native_rejects_nested_and_mixed_values() -> None:
    assert _neo4j_native(["AAPL", "MSFT"]) is True  # homogeneous primitive array
    assert _neo4j_native([]) is True
    assert _neo4j_native([1, "a"]) is False  # mixed-type array
    assert _neo4j_native([{"k": 1}]) is False  # list of maps
    assert _neo4j_native({"k": 1}) is False  # nested map


def test_encode_decode_round_trips_nested_props() -> None:
    props = {
        "ticker": "AAPL",
        "tickers": ["AAPL", "MSFT"],
        "snapshot": {"bars": [{"close": 1.0}], "news": {"AAPL": ["headline"]}},
    }
    encoded = _encode_props(props)
    assert encoded["ticker"] == "AAPL"  # native string untouched
    assert encoded["tickers"] == ["AAPL", "MSFT"]  # native array untouched
    assert isinstance(encoded["snapshot"], str)  # nested map JSON-encoded
    assert _decode_props(encoded) == props


def test_nested_props_survive_the_neo4j_store_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A nested-map property round-trips through Neo4j just like in-memory."""
    neo4j, _ = fake_neo4j_store(monkeypatch)
    postgres, _ = fake_postgres_store(monkeypatch)
    payload = {"snapshot": {"fundamentals": {"AAPL": {"pe": 35.7}}}}
    for graph in (InMemoryGraphStore(), neo4j, postgres):
        node = graph.merge_node("MarketData", "md-1", payload)
        assert node.props["snapshot"] == payload["snapshot"]


def test_postgres_list_nodes_keeps_key_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    postgres, _ = fake_postgres_store(monkeypatch)

    postgres.merge_node("Artifact", "b", {})
    postgres.merge_node("Artifact", "a", {})
    postgres.merge_node("Other", "c", {})

    assert [node.key for node in postgres.list_nodes("Artifact")] == ["a", "b"]


def _edge_walk(graph: GraphStore) -> tuple[list[str], list[str]]:
    parent = graph.merge_node("Artifact", "parent", {})
    child = graph.merge_node("Artifact", "child", {})
    graph.add_edge(parent, child, "DERIVED", {"run": "first"})
    graph.add_edge(parent, child, "DERIVED", {"run": "second"})
    return (
        [node.key for node in graph.descendants(parent, max_depth=1)],
        [node.key for node in graph.ancestors(child, max_depth=1)],
    )
