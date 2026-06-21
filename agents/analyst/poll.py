"""Analyst graph-poll work source (DL-08 / DL-08b).

Agent: analyst
Role: find ScanRun nodes the analyst has not processed yet and score them straight
      from the graph — reading the scanner's CandidateSet, the provider's MarketData
      (via the ScanRun's DERIVED_FROM lineage) and same-day RegimeContext — with no
      live bus RPC, so neither the scanner nor the provider need be alive.
External I/O: none (reads/writes the injected GraphStore).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.analyst.result import build_empty_result, incident_refs
from agents.analyst.run import run_analysis
from agents.analyst.settings import AnalystSettings
from contracts.provider import REGIME_CONTEXT_LABEL, MarketData, RegimeContext
from contracts.scanner import CandidateSet
from kernel import CollectingFaultSink

if TYPE_CHECKING:
    from contracts.analyst import RecommendationSet
    from kernel import FaultSink, GraphStore, Node

SCAN_RUN_LABEL = "ScanRun"
ANALYZED_EDGE = "ANALYZED_BY"
_DERIVED_FROM = "DERIVED_FROM"


def find_pending(graph: GraphStore) -> list[Node]:
    """Return ScanRun nodes with no downstream AnalystRun (unprocessed work)."""
    pending: list[Node] = []
    for node in graph.list_nodes(SCAN_RUN_LABEL):
        analyzed = list(
            graph.descendants(node, max_depth=1, edge_types={ANALYZED_EDGE})
        )
        if not analyzed:
            pending.append(node)
    return pending


def analyze_scan_node(
    node: Node,
    *,
    graph: GraphStore,
    settings: AnalystSettings | None = None,
    sink: FaultSink | None = None,
) -> None:
    """Analyze one ScanRun node from the graph and link the AnalystRun back to it."""
    settings = settings or AnalystSettings()
    sink = sink if sink is not None else CollectingFaultSink()
    candidate_set = CandidateSet.model_validate(node.props["candidate_set"])
    result = _run_from_graph(
        node, candidate_set, graph=graph, settings=settings, sink=sink
    )
    # Persist the full RecommendationSet on the AnalystRun so the PM can pull it from
    # the graph (DL-08b) instead of receiving it as a bus payload.
    analyst_run = graph.merge_node(
        "AnalystRun",
        result.run_id,
        {"recommendation_set": result.model_dump(mode="json")},
    )
    graph.add_edge(node, analyst_run, ANALYZED_EDGE)


def _run_from_graph(
    node: Node,
    candidate_set: CandidateSet,
    *,
    graph: GraphStore,
    settings: AnalystSettings,
    sink: FaultSink,
) -> RecommendationSet:
    if not candidate_set.candidates:
        return build_empty_result(
            graph, candidate_set, "scanner produced no candidates"
        )
    market_node = _market_node(graph, node)
    if market_node is None:
        return build_empty_result(graph, candidate_set, "provider data unavailable")
    market = MarketData.model_validate(market_node.props["snapshot"])
    regime = _regime(graph, market_node)
    if regime is None:
        return build_empty_result(graph, candidate_set, "provider data unavailable")
    refs = incident_refs(market, regime)
    return run_analysis(
        graph, candidate_set, market, regime, settings, sink, incident_refs=refs
    )


def _market_node(graph: GraphStore, scan_run: Node) -> Node | None:
    # write_scan adds the lineage edge as (scan)-[:DERIVED_FROM]->(market), so the
    # MarketData node the scanner consumed is the ScanRun's DERIVED_FROM descendant.
    return next(
        iter(graph.descendants(scan_run, max_depth=1, edge_types={_DERIVED_FROM})),
        None,
    )


def _regime(graph: GraphStore, market_node: Node) -> RegimeContext | None:
    key = f"regime-context:{market_node.props['window_end']}"
    node = graph.get_node(REGIME_CONTEXT_LABEL, key)
    return RegimeContext.model_validate(node.props["snapshot"]) if node else None
