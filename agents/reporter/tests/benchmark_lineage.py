"""Reporter benchmark lineage fixtures (S242, DL-246).

Agent: reporter
Role: give a PMRun the lineage the reporter's benchmark walks to its own run's
      MarketData, and a store that records every MarketData it hands out.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from collections.abc import Iterator

    from kernel import GraphStore, Node


def link_run_market(
    graph: GraphStore, pm_run_key: str, market: Node, *, run: str
) -> None:
    """PMRun.source_analyst_run_id -> AnalystRun <-ANALYZED_BY- ScanRun -> market."""
    analyst = graph.merge_node("AnalystRun", f"analyst-run-{run}", {})
    scan = graph.merge_node("ScanRun", f"scan-run-{run}", {})
    graph.add_edge(scan, analyst, "ANALYZED_BY")
    graph.add_edge(scan, market, "DERIVED_FROM")
    graph.merge_node("PMRun", pm_run_key, {"source_analyst_run_id": analyst.key})


class MarketDataSpy(InMemoryGraphStore):
    """Refuses a MarketData listing and records every MarketData node it returns."""

    def __init__(self) -> None:
        """An empty store with an empty read record."""
        super().__init__()
        self.read: list[str] = []

    def list_nodes(self, label: str) -> tuple[Node, ...]:
        """Listing every MarketData is the download the fix removed."""
        assert label != "MarketData", "the reporter listed every MarketData"
        return super().list_nodes(label)

    def get_node(self, label: str, key: str) -> Node | None:
        """Record a MarketData fetched by key."""
        return self._seen(super().get_node(label, key))

    def descendants(
        self, node: Node, *, max_depth: int, edge_types: set[str] | None = None
    ) -> Iterator[Node]:
        """Record each MarketData a downstream walk returns."""
        found = super().descendants(node, max_depth=max_depth, edge_types=edge_types)
        return iter([self._seen(item) for item in found])

    def ancestors(
        self, node: Node, *, max_depth: int, edge_types: set[str] | None = None
    ) -> Iterator[Node]:
        """Record each MarketData an upstream walk returns."""
        found = super().ancestors(node, max_depth=max_depth, edge_types=edge_types)
        return iter([self._seen(item) for item in found])

    def _seen[T: Node | None](self, node: T) -> T:
        if node is not None and node.label == "MarketData":
            self.read.append(node.key)
        return node
