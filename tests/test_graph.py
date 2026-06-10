"""In-memory GraphStore tests for the graph spine."""

from __future__ import annotations

import pytest

from kernel import (
    CollectingFaultSink,
    GraphStore,
    InMemoryGraphStore,
    Node,
)


def test_in_memory_merge_node_is_idempotent_and_append_only() -> None:
    store = InMemoryGraphStore()

    first = store.merge_node("Run", "r1", {"status": "new"})
    replay = store.merge_node("Run", "r1", {"status": "new"})
    enriched = store.merge_node("Run", "r1", {"status": "new", "score": 1})

    assert first == replay
    assert dict(enriched.props) == {"status": "new", "score": 1}
    assert store.get_node("Run", "r1") == enriched
    with pytest.raises(ValueError, match="cannot be overwritten"):
        store.merge_node("Run", "r1", {"status": "changed"})


def test_in_memory_merge_rejects_invalid_schema_changes() -> None:
    store = InMemoryGraphStore()

    with pytest.raises(ValueError, match="positive"):
        store.merge_node("Run", "bad", {}, schema_version=0)
    store.merge_node("Run", "r1", {}, schema_version=1)
    with pytest.raises(ValueError, match="schema_version"):
        store.merge_node("Run", "r1", {}, schema_version=2)


def test_in_memory_edges_and_traversal_depth() -> None:
    store = InMemoryGraphStore()
    root = store.merge_node("Artifact", "root", {})
    mid = store.merge_node("Artifact", "mid", {})
    leaf = store.merge_node("Artifact", "leaf", {})
    ignored = store.merge_node("Artifact", "ignored", {})

    store.add_edge(root, mid, "DERIVED")
    store.add_edge(root, mid, "DERIVED")
    store.add_edge(mid, leaf, "DERIVED")
    store.add_edge(ignored, leaf, "ANNOTATED")

    assert [node.key for node in store.ancestors(leaf, max_depth=2)] == [
        "mid",
        "ignored",
        "root",
    ]
    assert [
        node.key for node in store.ancestors(leaf, max_depth=2, edge_types={"DERIVED"})
    ] == ["mid", "root"]
    assert [node.key for node in store.descendants(root, max_depth=2)] == [
        "mid",
        "leaf",
    ]


def test_in_memory_traversal_depth_and_filter_misses() -> None:
    store = InMemoryGraphStore()
    parent = store.merge_node("Artifact", "parent", {})
    child = store.merge_node("Artifact", "child", {})
    store.add_edge(parent, child, "DERIVED")

    assert list(store.ancestors(child, max_depth=0)) == []
    assert list(store.ancestors(child, max_depth=1, edge_types={"OTHER"})) == []


def test_in_memory_traversal_deduplicates_converging_paths() -> None:
    store = InMemoryGraphStore()
    root = store.merge_node("Artifact", "root", {})
    left = store.merge_node("Artifact", "left", {})
    right = store.merge_node("Artifact", "right", {})
    leaf = store.merge_node("Artifact", "leaf", {})
    store.add_edge(root, left, "DERIVED")
    store.add_edge(root, right, "DERIVED")
    store.add_edge(left, leaf, "DERIVED")
    store.add_edge(right, leaf, "DERIVED")

    assert [node.key for node in store.descendants(root, max_depth=2)] == [
        "left",
        "right",
        "leaf",
    ]


def test_in_memory_failures_record_one_fault_and_reraise() -> None:
    sink = CollectingFaultSink()
    store = InMemoryGraphStore(sink)
    child = store.merge_node("Artifact", "child", {})

    with pytest.raises(KeyError):
        store.add_edge(Node("Missing", "parent"), child, "DERIVED")

    assert len(sink.faults) == 1
    fault = sink.faults[0]
    assert fault.source_agent == "kernel"
    assert fault.source_module == "kernel.graph"


def test_graph_store_protocol_exposes_no_destructive_operations() -> None:
    destructive = ("delete_node", "delete_edge", "drop_node", "drop_all", "remove")

    for name in destructive:
        assert not hasattr(GraphStore, name)
        assert not hasattr(InMemoryGraphStore, name)
