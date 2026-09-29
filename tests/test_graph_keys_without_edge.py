"""The key-and-edge query on the GraphStore port (S242, DL-246 D1-D3).

Agent: kernel
Role: prove keys_without_edge returns exactly the keys of a label's nodes with no
      edge of a type in a direction, in list_nodes order, with no props, and that the
      created_at bound keeps only the current ones.
External I/O: none (in-memory graph).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from kernel import InMemoryGraphStore
from kernel.graph_guarded import GuardedGraphStore
from kernel.graph_vocabulary import Vocabulary

NOW = datetime(2026, 9, 29, 23, 0, tzinfo=UTC)


def _graph() -> InMemoryGraphStore:
    graph = InMemoryGraphStore()
    for key in ("c", "a", "b", "d"):
        graph.merge_node("Run", key, {"payload": "x" * 64})
    graph.merge_node("Other", "e", {})
    done = graph.merge_node("Done", "done", {})
    runs = {node.key: node for node in graph.list_nodes("Run")}
    graph.add_edge(runs["a"], done, "DONE_BY")
    graph.add_edge(done, runs["d"], "DONE_BY")
    graph.add_edge(runs["b"], done, "OTHER_EDGE")
    return graph


def test_keys_without_an_outgoing_edge_come_back_in_list_order() -> None:
    """DL-246 D1/D3: keys only, in list_nodes order, the edge either way decides."""
    graph = _graph()

    keys = graph.keys_without_edge("Run", "DONE_BY")

    assert keys == ("c", "b", "d")
    listed = tuple(node.key for node in graph.list_nodes("Run"))
    assert keys == tuple(key for key in listed if key != "a")
    assert all(type(key) is str for key in keys)
    assert graph.keys_without_edge("Run", "DONE_BY", downstream=False) == (
        "c",
        "a",
        "b",
    )
    assert graph.keys_without_edge("Missing", "DONE_BY") == ()


def test_the_created_at_bound_keeps_only_current_nodes() -> None:
    """DL-246 D2: at or after the instant; missing, non-string or older is out."""
    graph = InMemoryGraphStore()
    edge = NOW - timedelta(hours=24)
    old = edge - timedelta(seconds=1)
    micro = edge + timedelta(microseconds=1)
    graph.merge_node("Run", "old", {"created_at": old.isoformat()})
    graph.merge_node("Run", "edge", {"created_at": edge.isoformat()})
    graph.merge_node("Run", "micro", {"created_at": micro.isoformat()})
    graph.merge_node("Run", "undated", {})
    graph.merge_node("Run", "number", {"created_at": 1})
    graph.merge_node("Run", "fresh", {"created_at": NOW.isoformat()})

    keys = graph.keys_without_edge("Run", "DONE_BY", created_at_from=edge)

    assert keys == ("edge", "micro", "fresh")
    assert graph.keys_without_edge("Run", "DONE_BY") == (
        "old",
        "edge",
        "micro",
        "undated",
        "number",
        "fresh",
    )


def test_the_bound_compares_in_utc_and_refuses_a_naive_instant() -> None:
    """DL-246 D2: an aware instant in another zone is the same bound; naive fails."""
    graph = InMemoryGraphStore()
    graph.merge_node("Run", "fresh", {"created_at": NOW.isoformat()})
    sydney = NOW.astimezone(timezone(timedelta(hours=10)))

    assert graph.keys_without_edge("Run", "E", created_at_from=sydney) == ("fresh",)
    with pytest.raises(ValueError, match="timezone-aware"):
        graph.keys_without_edge("Run", "E", created_at_from=NOW.replace(tzinfo=None))


def test_the_guarded_store_reads_through() -> None:
    """DL-246 D1: the vocabulary guard only ever says no to writes."""
    graph = _graph()
    guarded = GuardedGraphStore(graph, Vocabulary.from_mapping({}))

    assert guarded.keys_without_edge("Run", "DONE_BY") == ("c", "b", "d")
    assert (
        guarded.keys_without_edge(
            "Run", "DONE_BY", downstream=False, created_at_from=NOW
        )
        == ()
    )
