"""Scanner graph-poll work source (DL-08 / DL-08b).

Agent: scanner
Role: find provider MarketData nodes the scanner has not processed yet and scan
      them straight from the graph — no live bus RPC, so the provider container
      need not be alive.
External I/O: none (reads/writes the injected GraphStore).
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from agents.scanner.domain.filters import apply_filters
from agents.scanner.domain.ranking import rank_survivors
from agents.scanner.results import scan_explanation
from agents.scanner.store import write_scan
from contracts.provider import MARKET_DATA_LABEL, MarketData
from contracts.scanner import CandidateSet

if TYPE_CHECKING:
    from agents.scanner.settings import ScannerSettings
    from kernel import GraphStore, Node

SCANNED_EDGE = "SCANNED_BY"
_DEFAULT_UNIVERSE_NAME = "sp500"


def find_pending(graph: GraphStore) -> list[Node]:
    """Return MarketData nodes with no downstream ScanRun (unprocessed work)."""
    pending: list[Node] = []
    for node in graph.list_nodes(MARKET_DATA_LABEL):
        scanned = list(graph.descendants(node, max_depth=1, edge_types={SCANNED_EDGE}))
        if not scanned:
            pending.append(node)
    return pending


def scan_market_node(
    node: Node, *, graph: GraphStore, settings: ScannerSettings
) -> None:
    """Scan one provider MarketData node and link the ScanRun back to it."""
    market = MarketData.model_validate(node.props["snapshot"])
    tickers = tuple(str(ticker) for ticker in node.props["tickers"])
    window_end = date.fromisoformat(str(node.props["window_end"]))
    survivors, trace = apply_filters(
        tickers,
        market.bars,
        market.benchmark,
        market.earnings,
        window_end,
        settings,
    )
    candidates = rank_survivors(survivors, cap=settings.candidate_cap)
    provenance = write_scan(
        graph,
        universe=_DEFAULT_UNIVERSE_NAME,
        candidates=candidates,
        trace=trace,
        provider_graph_node_id=f"{node.label}:{node.key}",
    )
    # Persist the full CandidateSet on the ScanRun so the analyst can pull it from
    # the graph (DL-08b) instead of receiving it as a bus payload.
    candidate_set = CandidateSet(
        run_id=provenance.run_id,
        candidates=candidates,
        filter_trace=trace,
        explanation=scan_explanation(candidates, trace),
        provenance=provenance,
    )
    scan_run = graph.merge_node(
        "ScanRun",
        provenance.run_id,
        {"candidate_set": candidate_set.model_dump(mode="json")},
    )
    graph.add_edge(node, scan_run, SCANNED_EDGE)
