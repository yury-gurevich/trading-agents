"""An analysed ScanRun is marked processed (moved from test_analyst_poll, S251).

Agent: analyst
Role: prove the graph-pull poll links an analysed ScanRun, so it is never work again.
External I/O: none (in-memory graph).
"""

from __future__ import annotations

from agents.analyst.poll import analyze_scan_node, find_pending
from agents.analyst.tests.test_analyst_poll import _seed_scan_run
from kernel import InMemoryGraphStore


def test_analyze_scan_node_marks_node_processed() -> None:
    """ANLZ-TRG-02 (graph-pull): an analysed ScanRun is linked, so never work again."""
    graph = InMemoryGraphStore()
    node = _seed_scan_run(graph)
    analyze_scan_node(node, graph=graph)
    assert find_pending(graph) == []
