"""Scanner graph-store tests.

Agent: scanner
Role: verify scanner graph writes tolerate absent upstream nodes.
External I/O: none.
"""

from __future__ import annotations

from agents.scanner.store import write_scan
from contracts.scanner import FilterTrace
from kernel import InMemoryGraphStore


def test_write_scan_ignores_missing_provider_reference() -> None:
    graph = InMemoryGraphStore()

    provenance = write_scan(
        graph,
        universe="fixture",
        candidates=(),
        trace=FilterTrace(universe_size=1, evaluated=1),
        provider_graph_node_id="MarketSnapshot:missing",
    )

    assert provenance.graph_node_id is not None
    scan_key = provenance.graph_node_id.split(":", 1)[1]
    scan = graph.get_node("ScanRun", scan_key)
    assert scan is not None
    assert list(graph.descendants(scan, max_depth=1, edge_types={"DERIVED_FROM"})) == []
