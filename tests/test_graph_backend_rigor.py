"""GraphStore backend rigor parity tests.

Agent: kernel
Role: verify shared graph semantics across in-memory and Neo4j backends.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.graph_neo4j_fakes import store as fake_store

from kernel import GraphStore, InMemoryGraphStore

if TYPE_CHECKING:
    import pytest


def test_edge_identity_matches_between_backends(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    neo4j, fake_driver = fake_store(monkeypatch)
    memory = InMemoryGraphStore()

    assert _edge_walk(memory) == _edge_walk(neo4j)
    assert len(memory._edges) == 1
    assert len(fake_driver.edges) == 1
    assert fake_driver.edges[0][3] == {"run": "first"}


def test_neo4j_constraints_are_installed_once_per_label(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph, fake_driver = fake_store(monkeypatch)

    graph.merge_node("Artifact", "one", {})
    graph.merge_node("Artifact", "two", {})
    graph.merge_node("OtherArtifact", "one", {})

    assert fake_driver.constraints == [
        "CREATE CONSTRAINT `Artifact_key_unique` IF NOT EXISTS "
        "FOR (n:`Artifact`) REQUIRE n.key IS UNIQUE",
        "CREATE CONSTRAINT `OtherArtifact_key_unique` IF NOT EXISTS "
        "FOR (n:`OtherArtifact`) REQUIRE n.key IS UNIQUE",
    ]


def _edge_walk(graph: GraphStore) -> tuple[list[str], list[str]]:
    parent = graph.merge_node("Artifact", "parent", {})
    child = graph.merge_node("Artifact", "child", {})
    graph.add_edge(parent, child, "DERIVED", {"run": "first"})
    graph.add_edge(parent, child, "DERIVED", {"run": "second"})
    return (
        [node.key for node in graph.descendants(parent, max_depth=1)],
        [node.key for node in graph.ancestors(child, max_depth=1)],
    )
