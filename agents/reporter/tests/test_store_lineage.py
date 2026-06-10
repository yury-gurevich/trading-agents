"""Reporter store and lineage tests.

Agent: reporter
Role: verify reporter graph writes and read-only traversal helpers.
External I/O: none.
"""

from __future__ import annotations

from agents.reporter.domain.lineage import (
    collect_run_lineage,
    collect_trade_lineage,
    run_id,
)
from agents.reporter.store import write_snapshot, write_trade_narrative
from agents.reporter.tests.helpers import (
    POSITION_ID,
    RUN_ID,
    has_edge,
    seed_full_graph,
    seed_position_only,
)
from kernel import InMemoryGraphStore


def test_store_writes_snapshot_and_narrative_edges_when_targets_exist() -> None:
    graph = InMemoryGraphStore()
    seed_full_graph(graph)
    snapshot = write_snapshot(
        graph,
        run_id=RUN_ID,
        metrics_blob={"portfolio": {"positions_opened": 1.0}},
        headline_summary="headline",
    )
    narrative = write_trade_narrative(
        graph, run_id=RUN_ID, position_id=POSITION_ID, story="AAPL story"
    )
    assert snapshot.graph_node_id == f"Snapshot:snapshot:{RUN_ID}"
    assert narrative.graph_node_id == f"TradeNarrative:narrative:{POSITION_ID}"
    assert has_edge(
        graph, ("Snapshot", f"snapshot:{RUN_ID}"), ("PMRun", RUN_ID), "SUMMARISES"
    )
    assert has_edge(
        graph,
        ("TradeNarrative", f"narrative:{POSITION_ID}"),
        ("Position", POSITION_ID),
        "NARRATES",
    )


def test_store_skips_edges_when_targets_are_missing() -> None:
    graph = InMemoryGraphStore()
    write_snapshot(graph, run_id="missing", metrics_blob={}, headline_summary="x")
    write_trade_narrative(
        graph, run_id="missing", position_id="missing:AAPL", story="x"
    )
    assert len(graph._edges) == 0


def test_lineage_collects_full_run_and_trade_paths() -> None:
    graph = InMemoryGraphStore()
    seed_full_graph(graph)
    pm_run = graph.get_node("PMRun", RUN_ID)
    position = graph.get_node("Position", POSITION_ID)
    assert pm_run is not None
    assert position is not None
    run_lineage = collect_run_lineage(graph, pm_run)
    trade_lineage = collect_trade_lineage(graph, position)
    assert [node.label for node in run_lineage.orders] == ["OrderIntent"]
    assert [node.label for node in run_lineage.market_snapshots] == ["MarketSnapshot"]
    assert trade_lineage.close_decision is not None
    assert run_id(position) == RUN_ID


def test_lineage_handles_missing_optional_legs() -> None:
    graph = InMemoryGraphStore()
    seed_position_only(graph)
    position = graph.get_node("Position", POSITION_ID)
    assert position is not None
    trade_lineage = collect_trade_lineage(graph, position)
    assert trade_lineage.fill is None
    assert run_id(position) == RUN_ID

    pm_run = graph.merge_node("PMRun", "pm-run-empty", {})
    recommendation = graph.merge_node("Recommendation", "rec", {})
    orphan_recommendation = graph.merge_node("Recommendation", "orphan-rec", {})
    candidate = graph.merge_node("Candidate", "candidate", {})
    order = graph.merge_node("OrderIntent", "order", {})
    orphan_order = graph.merge_node("OrderIntent", "orphan-order", {})
    graph.add_edge(order, pm_run, "EMITTED_BY")
    graph.add_edge(orphan_order, pm_run, "EMITTED_BY")
    graph.add_edge(order, recommendation, "APPROVES")
    graph.add_edge(orphan_order, orphan_recommendation, "APPROVES")
    graph.add_edge(recommendation, candidate, "DERIVED_FROM")
    run_lineage = collect_run_lineage(graph, pm_run)
    assert run_lineage.scan_runs == ()
    assert run_lineage.market_snapshots == ()
