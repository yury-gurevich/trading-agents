"""GraphStore backend rigor parity tests.

Agent: kernel
Role: verify shared graph semantics across in-memory and PostgreSQL backends.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.graph_postgres_fakes import store as fake_postgres_store

from kernel import GraphStore, InMemoryGraphStore

if TYPE_CHECKING:
    import pytest


def test_edge_identity_matches_between_backends(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    postgres, fake_postgres = fake_postgres_store(monkeypatch)
    memory = InMemoryGraphStore()

    assert _edge_walk(memory) == _edge_walk(postgres)
    assert len(memory._edges) == 1
    assert len(fake_postgres.edges) == 1
    assert fake_postgres.edges[0][3] == {"run": "first"}


def test_nested_props_survive_live_store_boundaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A nested-map property round-trips through PostgreSQL just like in-memory."""
    postgres, _ = fake_postgres_store(monkeypatch)
    payload = {"snapshot": {"fundamentals": {"AAPL": {"pe": 35.7}}}}
    for graph in (InMemoryGraphStore(), postgres):
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
