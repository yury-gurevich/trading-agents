"""Dashboard projection read cache.

Agent: surfaces
Role: cache short-lived read-model payloads so rapid dashboard refreshes do not
      repeat identical GraphStore reads.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import TYPE_CHECKING, TypeVar, cast

T = TypeVar("T")

if TYPE_CHECKING:
    from collections.abc import Callable, Hashable, Iterator

    from kernel import GraphStore, Node
    from kernel.graph_support import Props


@dataclass(frozen=True)
class CacheStats:
    """Projection cache counters for tests and live evidence scripts."""

    hits: int
    misses: int


@dataclass(frozen=True)
class _Entry:
    created_at: float
    payload: object


class ProjectionReadCache:
    """Tiny per-process TTL cache for JSON-ready dashboard projection payloads."""

    def __init__(
        self, ttl_seconds: float, *, now: Callable[[], float] = monotonic
    ) -> None:
        """Create a cache; ``ttl_seconds <= 0`` disables storage."""
        self.ttl_seconds = ttl_seconds
        self._now = now
        self._items: dict[Hashable, _Entry] = {}
        self._hits = 0
        self._misses = 0

    @property
    def stats(self) -> CacheStats:
        """Return hit/miss counters for observable cache proof."""
        return CacheStats(hits=self._hits, misses=self._misses)

    def read(self, key: Hashable, build: Callable[[], T]) -> T:
        """Return a cached payload when it is still inside the TTL."""
        if self.ttl_seconds <= 0:
            self._misses += 1
            return build()
        now = self._now()
        entry = self._items.get(key)
        if entry is not None and now - entry.created_at <= self.ttl_seconds:
            self._hits += 1
            return cast("T", entry.payload)
        self._misses += 1
        payload = build()
        self._items[key] = _Entry(now, payload)
        return payload

    def clear(self) -> None:
        """Drop cached entries after a write passes through the wrapper."""
        self._items.clear()


class CachingGraphStore:
    """GraphStore read-through cache for dashboard projection reads."""

    def __init__(
        self,
        inner: GraphStore,
        ttl_seconds: float,
        *,
        now: Callable[[], float] = monotonic,
    ) -> None:
        """Wrap a graph; ``ttl_seconds <= 0`` disables cache hits."""
        self._inner = inner
        self._cache = ProjectionReadCache(ttl_seconds, now=now)

    @property
    def stats(self) -> CacheStats:
        """Expose cache counters for tests and live evidence scripts."""
        return self._cache.stats

    def merge_node(
        self, label: str, key: str, props: Props, *, schema_version: int = 1
    ) -> Node:
        """Pass through writes and invalidate stale read entries."""
        node = self._inner.merge_node(label, key, props, schema_version=schema_version)
        self._cache.clear()
        return node

    def add_edge(
        self, parent: Node, child: Node, edge_type: str, props: Props | None = None
    ) -> None:
        """Pass through writes and invalidate stale lineage entries."""
        self._inner.add_edge(parent, child, edge_type, props)
        self._cache.clear()

    def get_node(self, label: str, key: str) -> Node | None:
        """Return a cached node lookup within the TTL."""
        return self._cache.read(
            ("get_node", label, key), lambda: self._inner.get_node(label, key)
        )

    def list_nodes(self, label: str) -> tuple[Node, ...]:
        """Return cached label scans within the TTL."""
        return self._cache.read(
            ("list_nodes", label), lambda: self._inner.list_nodes(label)
        )

    def ancestors(
        self, node: Node, *, max_depth: int, edge_types: set[str] | None = None
    ) -> Iterator[Node]:
        """Return cached upstream lineage walks within the TTL."""
        key = ("ancestors", node.label, node.key, max_depth, _edge_key(edge_types))
        return iter(
            self._cache.read(
                key,
                lambda: tuple(
                    self._inner.ancestors(
                        node, max_depth=max_depth, edge_types=edge_types
                    )
                ),
            )
        )

    def descendants(
        self, node: Node, *, max_depth: int, edge_types: set[str] | None = None
    ) -> Iterator[Node]:
        """Return cached downstream lineage walks within the TTL."""
        key = ("descendants", node.label, node.key, max_depth, _edge_key(edge_types))
        return iter(
            self._cache.read(
                key,
                lambda: tuple(
                    self._inner.descendants(
                        node, max_depth=max_depth, edge_types=edge_types
                    )
                ),
            )
        )


def _edge_key(edge_types: set[str] | None) -> tuple[str, ...]:
    return ("*",) if edge_types is None else tuple(sorted(edge_types))
