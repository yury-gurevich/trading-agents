"""Scanner graph-poll find_pending + scan_market_node tests.

Agent: scanner
Role: verify the scanner finds unprocessed MarketData nodes and scans them from
      the graph (no bus RPC), marking each processed so it is not re-scanned.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.scanner.poll import find_pending, scan_market_node
from agents.scanner.settings import ScannerSettings
from contracts.common import Provenance
from contracts.provider import MARKET_DATA_LABEL, DataQualityTrace, MarketData
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from kernel import GraphStore, Node


def _seed_market_node(
    graph: GraphStore,
    key: str = "market-data:2026-01-05",
    tickers: tuple[str, ...] = ("AAPL",),
) -> Node:
    market = MarketData(
        bars=(),
        quality=DataQualityTrace(requested=0, returned=0),
        provenance=Provenance(run_id="provider-1", source_agent="provider"),
    )
    return graph.merge_node(
        MARKET_DATA_LABEL,
        key,
        {
            "snapshot": market.model_dump(mode="json"),
            "tickers": list(tickers),
            "window_end": "2026-01-05",
        },
    )


def test_find_pending_returns_unscanned_market_data() -> None:
    graph = InMemoryGraphStore()
    _seed_market_node(graph)
    assert len(find_pending(graph)) == 1


def test_find_pending_empty_when_no_market_data() -> None:
    graph = InMemoryGraphStore()
    assert find_pending(graph) == []


def test_scan_market_node_writes_scan_run() -> None:
    graph = InMemoryGraphStore()
    node = _seed_market_node(graph)
    scan_market_node(node, graph=graph, settings=ScannerSettings())
    assert len(graph.list_nodes("ScanRun")) == 1


def test_scan_market_node_marks_node_processed() -> None:
    graph = InMemoryGraphStore()
    node = _seed_market_node(graph)
    scan_market_node(node, graph=graph, settings=ScannerSettings())
    assert find_pending(graph) == []
