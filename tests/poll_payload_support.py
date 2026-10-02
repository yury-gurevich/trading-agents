"""Shared payload spy and case shape for graph-pull finder proofs.

Agent: tooling
Role: refuse whole-label downloads and processed-edge walks without changing S242's spy.
External I/O: none (in-memory graph).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from datetime import tzinfo

    from kernel import GraphStore, Node

NOW = datetime(2026, 9, 29, 23, 0, tzinfo=UTC)


class PayloadSpy(InMemoryGraphStore):
    """An in-memory store that refuses a poll's payload-download shapes when armed."""

    def __init__(self) -> None:
        """Start disarmed so a fixture can be seeded with the ordinary API."""
        super().__init__()
        self.label = ""
        self.edge = ""
        self.fetched: list[str] = []

    def arm(self, label: str, edge: str) -> None:
        """From now on, listing ``label`` or walking ``edge`` from it fails the test."""
        self.label, self.edge = label, edge

    def list_nodes(self, label: str) -> tuple[Node, ...]:
        """Refuse the whole-label download the fix removed."""
        assert label != self.label, f"poll listed every {label} with its props"
        return super().list_nodes(label)

    def get_node(self, label: str, key: str) -> Node | None:
        """Record every node of the poll's label fetched by key."""
        if label == self.label:
            self.fetched.append(key)
        return super().get_node(label, key)

    def descendants(
        self, node: Node, *, max_depth: int, edge_types: set[str] | None = None
    ) -> Iterator[Node]:
        """Refuse the per-node processed-edge walk the fix removed."""
        self._refuse_walk(node, edge_types)
        return super().descendants(node, max_depth=max_depth, edge_types=edge_types)

    def ancestors(
        self, node: Node, *, max_depth: int, edge_types: set[str] | None = None
    ) -> Iterator[Node]:
        """Refuse the processed-edge walk upstream too."""
        self._refuse_walk(node, edge_types)
        return super().ancestors(node, max_depth=max_depth, edge_types=edge_types)

    def _refuse_walk(self, node: Node, edge_types: set[str] | None) -> None:
        if node.label != self.label:
            return
        assert edge_types is not None, f"poll walked every edge of a {node.label}"
        assert self.edge not in edge_types, f"poll walked {self.edge} per node"


@dataclass(frozen=True)
class PollCase:
    """One poll: its label and processed edge, a seeder, and what it must find."""

    name: str
    label: str
    edge: str
    seed: Callable[[GraphStore], None]
    candidates: tuple[str, ...]
    pending: tuple[str, ...]


def seed_chain(graph: GraphStore, label: str, done_edge: str, child: str) -> None:
    """Three nodes of ``label``; ``b`` already processed through ``done_edge``."""
    for key in ("c", "b", "a"):
        graph.merge_node(label, key, {"payload": "x" * 256})
    done = graph.merge_node(child, "done", {})
    parent = graph.get_node(label, "b")
    assert parent is not None
    graph.add_edge(parent, done, done_edge)


class FrozenDatetime(datetime):
    """Pin execution's poll clock to the synthetic PM runs, independent of run date."""

    @classmethod
    def now(cls, tz: tzinfo | None = None) -> datetime:
        return NOW if tz is None else NOW.astimezone(tz)
