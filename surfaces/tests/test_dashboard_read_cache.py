"""Dashboard projection read-cache tests.

Agent: surfaces
Role: verify the graph read cache cuts repeated projection reads without hiding
      changes past its TTL or when disabled.
External I/O: none.
"""

from __future__ import annotations

from kernel import InMemoryGraphStore
from surfaces.dashboard.read_cache import CachingGraphStore, ProjectionReadCache


class _Clock:
    """Mutable monotonic clock for deterministic TTL tests."""

    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value


def test_projection_cache_hit_expiry_and_disable_truth_table() -> None:
    clock = _Clock()
    calls = 0

    def build() -> int:
        nonlocal calls
        calls += 1
        return calls

    cache = ProjectionReadCache(2.0, now=clock)
    assert cache.read("runs", build) == 1
    assert cache.read("runs", build) == 1
    assert cache.stats.hits == 1
    assert cache.stats.misses == 1

    clock.value = 2.1
    assert cache.read("runs", build) == 2
    assert cache.stats.hits == 1
    assert cache.stats.misses == 2

    disabled = ProjectionReadCache(0.0, now=clock)
    assert disabled.read("runs", build) == 3
    assert disabled.read("runs", build) == 4
    assert disabled.stats.hits == 0
    assert disabled.stats.misses == 2


def test_caching_graph_store_refreshes_verdict_inputs_after_ttl() -> None:
    clock = _Clock()
    graph = InMemoryGraphStore()
    graph.merge_node("RunRequest", "run-request:one", {"run_id": "one"})
    cached = CachingGraphStore(graph, 2.0, now=clock)

    assert [node.key for node in cached.list_nodes("RunRequest")] == ["run-request:one"]
    graph.merge_node("RunRequest", "run-request:two", {"run_id": "two"})
    assert [node.key for node in cached.list_nodes("RunRequest")] == ["run-request:one"]

    clock.value = 2.1
    assert [node.key for node in cached.list_nodes("RunRequest")] == [
        "run-request:one",
        "run-request:two",
    ]


def test_caching_graph_store_caches_node_and_lineage_reads() -> None:
    clock = _Clock()
    graph = InMemoryGraphStore()
    parent = graph.merge_node("Parent", "p", {})
    child = graph.merge_node("Child", "c", {})
    graph.add_edge(parent, child, "LINK")
    cached = CachingGraphStore(graph, 5.0, now=clock)

    assert cached.get_node("Parent", "p") == parent
    assert cached.get_node("Parent", "p") == parent
    assert tuple(cached.descendants(parent, max_depth=1, edge_types={"LINK"})) == (
        child,
    )
    assert tuple(cached.descendants(parent, max_depth=1, edge_types={"LINK"})) == (
        child,
    )
    assert tuple(cached.ancestors(child, max_depth=1)) == (parent,)
    assert tuple(cached.ancestors(child, max_depth=1)) == (parent,)

    assert cached.stats.hits == 3
    assert cached.stats.misses == 3


def test_caching_graph_store_write_through_clears_stale_entries() -> None:
    cached = CachingGraphStore(InMemoryGraphStore(), 5.0)
    parent = cached.merge_node("Parent", "p", {})
    assert cached.list_nodes("Child") == ()

    child = cached.merge_node("Child", "c", {})
    cached.add_edge(parent, child, "LINK")

    assert cached.list_nodes("Child") == (child,)
    assert tuple(cached.descendants(parent, max_depth=1)) == (child,)
