"""Graph fixtures and a payload spy for the seven graph-pull polls (S242, DL-246).

Agent: tooling
Role: seed each poll's work (done, pending and not-yet-ready items), and a store that
      fails a test when a poll lists its own label with props or walks its own
      processed edge, and records which of its label's nodes it fetched by key.
External I/O: none (in-memory graph).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from agents.provider.tests.barrier_history_helpers import analyst_run, rec
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

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


def _chain(graph: GraphStore, label: str, done_edge: str, child: str) -> None:
    """Three nodes of ``label``; ``b`` already processed through ``done_edge``."""
    for key in ("c", "b", "a"):
        graph.merge_node(label, key, {"payload": "x" * 256})
    done = graph.merge_node(child, "done", {})
    parent = graph.get_node(label, "b")
    assert parent is not None
    graph.add_edge(parent, done, done_edge)


def seed_analyst(graph: GraphStore) -> None:
    """ScanRuns: synced (pending), analysed, unsynced, and with no MarketData."""
    _chain(graph, "ScanRun", "ANALYZED_BY", "AnalystRun")
    graph.merge_node("ScanRun", "d", {})
    for scan, run_id in (("c", "synced"), ("b", "synced"), ("a", "unsynced")):
        market = graph.merge_node("MarketData", f"md-{scan}", {"run_id": run_id})
        node = graph.get_node("ScanRun", scan)
        assert node is not None
        graph.add_edge(node, market, "DERIVED_FROM")
    request = graph.merge_node("RunRequest", "run-request:synced", {})
    marker = graph.merge_node(
        "MonitorRun",
        "position-sync:synced",
        {"phase": "sync", "position_book_status": "fresh"},
    )
    graph.add_edge(request, marker, "POSITION_SYNCED_BY")


def seed_reporter(graph: GraphStore) -> None:
    """MonitorRuns: a sync marker (never reported), one pending, one reported."""
    graph.merge_node("MonitorRun", "sync", {"phase": "sync"})
    _chain(graph, "MonitorRun", "REPORTED_BY", "Snapshot")


def seed_barrier(graph: GraphStore) -> None:
    """71 stale AnalystRuns with a qualifying buy, and one current (A8)."""
    stale = (NOW - timedelta(days=2)).isoformat()
    for index in range(71):
        key = f"stale-{index:02d}"
        analyst_run(graph, rec("AAPL", "buy"), key=key)
        graph.merge_node("AnalystRun", key, {"created_at": stale})
    analyst_run(graph, rec("AAPL", "buy"), key="current")
    current = (NOW - timedelta(hours=1)).isoformat()
    graph.merge_node("AnalystRun", "current", {"created_at": current})


def _simple(name: str, label: str, edge: str) -> PollCase:
    return PollCase(
        name,
        label,
        edge,
        lambda graph: _chain(graph, label, edge, "Done"),
        ("c", "a"),
        ("c", "a"),
    )


CASES = (
    _simple("provider", "RunRequest", "INGESTED_BY"),
    _simple("scanner", "MarketData", "SCANNED_BY"),
    PollCase(
        "analyst", "ScanRun", "ANALYZED_BY", seed_analyst, ("c", "a", "d"), ("c",)
    ),
    _simple("portfolio_manager", "AnalystRun", "EVALUATED_BY"),
    _simple("monitor", "ExecutionRun", "MONITORED_BY"),
    PollCase(
        "reporter",
        "MonitorRun",
        "REPORTED_BY",
        seed_reporter,
        ("sync", "c", "a"),
        ("c", "a"),
    ),
    PollCase(
        "barrier_history",
        "AnalystRun",
        "BARRIER_HISTORY_BY",
        seed_barrier,
        ("current",),
        ("current",),
    ),
)
