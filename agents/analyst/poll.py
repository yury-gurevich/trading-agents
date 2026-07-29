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
from contracts.position_sync import (
    POSITION_BOOK_STALE_INCIDENT,
    PositionBookSyncState,
    position_book_sync_attempted,
    position_book_sync_state,
)
from contracts.positions import open_positions
from contracts.provider import REGIME_CONTEXT_LABEL, MarketData, RegimeContext
from contracts.scanner import CandidateSet
from kernel import CollectingFaultSink, fault_boundary
from kernel.fault_graph import GraphFaultSink

if TYPE_CHECKING:
    from contracts.analyst import RecommendationSet
    from kernel import FaultSink, GraphStore, Node

SCAN_RUN_LABEL = "ScanRun"
ANALYZED_EDGE = "ANALYZED_BY"
_DERIVED_FROM = "DERIVED_FROM"


def find_pending(graph: GraphStore) -> list[Node]:
    """Return synced ScanRun nodes with no downstream AnalystRun."""
    pending: list[Node] = []
    for node in graph.list_nodes(SCAN_RUN_LABEL):
        analyzed = list(
            graph.descendants(node, max_depth=1, edge_types={ANALYZED_EDGE})
        )
        if not analyzed and _book_sync_attempted(graph, node):
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
    sink = sink if sink is not None else GraphFaultSink(graph, CollectingFaultSink())
    candidate_set = CandidateSet.model_validate(node.props["candidate_set"])
    sync = _book_sync_state(graph, node)
    if sync is None and _market_node(graph, node) is not None:
        return
    result = _run_from_graph(
        node, candidate_set, graph=graph, settings=settings, sink=sink, sync=sync
    )
    # Persist the full RecommendationSet on the AnalystRun so the PM can pull it from
    # the graph (DL-08b) instead of receiving it as a bus payload.
    props: dict[str, object] = {"recommendation_set": result.model_dump(mode="json")}
    if sync is not None:
        props["position_book_status"] = sync.status
        if sync.stale_reason:
            props["position_book_stale_reason"] = sync.stale_reason
    analyst_run = graph.merge_node("AnalystRun", result.run_id, props)
    graph.add_edge(node, analyst_run, ANALYZED_EDGE)


def _run_from_graph(
    node: Node,
    candidate_set: CandidateSet,
    *,
    graph: GraphStore,
    settings: AnalystSettings,
    sink: FaultSink,
    sync: PositionBookSyncState | None,
) -> RecommendationSet:
    stale_refs: tuple[str, ...] = ()
    if sync is not None and sync.status == "stale":
        _record_stale_book(sink, sync.stale_reason)
        stale_refs = (POSITION_BOOK_STALE_INCIDENT,)
    held = open_positions(graph)
    if not candidate_set.candidates and not held:
        return build_empty_result(
            graph,
            candidate_set,
            "scanner produced no candidates",
            stale_refs,
        )
    market_node = _market_node(graph, node)
    if market_node is None:
        return build_empty_result(graph, candidate_set, "provider data unavailable")
    market = MarketData.model_validate(market_node.props["snapshot"])
    regime = _regime(graph, market_node)
    if regime is None:
        return build_empty_result(graph, candidate_set, "provider data unavailable")
    refs = (*incident_refs(market, regime), *stale_refs)
    return run_analysis(
        graph,
        candidate_set,
        market,
        regime,
        settings,
        sink,
        incident_refs=refs,
        held_positions=held,
    )


def _book_sync_attempted(graph: GraphStore, scan_run: Node) -> bool:
    market_node = _market_node(graph, scan_run)
    if market_node is None:
        return False
    return position_book_sync_attempted(graph, str(market_node.props.get("run_id", "")))


def _book_sync_state(graph: GraphStore, scan_run: Node) -> PositionBookSyncState | None:
    market_node = _market_node(graph, scan_run)
    if market_node is None:
        return None
    return position_book_sync_state(graph, str(market_node.props.get("run_id", "")))


def _record_stale_book(sink: FaultSink, reason: str | None) -> None:
    message = f"position book stale: {reason or 'broker snapshot was stale'}"
    with fault_boundary(
        sink,
        agent="analyst",
        module="agents.analyst.poll",
        capability="position_book_sync",
        reraise=False,
    ):
        raise RuntimeError(message)


def _market_node(graph: GraphStore, scan_run: Node) -> Node | None:
    # write_scan adds the lineage edge as (scan)-[:DERIVED_FROM]->(market), so the
    # MarketData node the scanner consumed is the ScanRun's DERIVED_FROM descendant.
    return next(
        iter(graph.descendants(scan_run, max_depth=1, edge_types={_DERIVED_FROM})),
        None,
    )


def _regime(graph: GraphStore, market_node: Node) -> RegimeContext | None:
    key = f"regime-context:{market_node.props['run_id']}"
    node = graph.get_node(REGIME_CONTEXT_LABEL, key)
    return RegimeContext.model_validate(node.props["snapshot"]) if node else None
