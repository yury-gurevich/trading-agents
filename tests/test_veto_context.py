"""Deliberation veto evidence-context tests.

Agent: orchestration
Role: verify the veto prompt renderer carries upstream graph evidence into debate.
External I/O: none.
"""

from __future__ import annotations

from tests.veto_context_fixtures import (
    candidates,
    intent,
    linked_graph,
    market_data,
    order_set,
    recs,
)

from kernel import InMemoryGraphStore
from orchestration.veto_context import build_veto_context


def test_full_context_includes_all_available_upstream_evidence() -> None:
    graph = InMemoryGraphStore()
    item = intent(stop=0.03, target=0.08)
    orders = order_set(item, refs=("pm-ref",))
    pm = linked_graph(graph, full=True)

    context = build_veto_context(graph, pm, orders, item)

    assert "PM order: action=buy; ticker=AAPL; quantity=7" in context
    assert "refs=['pm-ref']" in context
    assert "Analyst recommendation for AAPL" in context
    assert "sentiment_score=0.700" in context
    assert "fundamental_score=0.650" in context
    assert "Analyst rejected AAPL: duplicate exposure" in context
    assert "Scanner candidate for AAPL: rank=1; score=0.810" in context
    assert "Scanner verdict for AAPL: decision=survived" in context
    assert "features={beta=1.1, return_5d=0.08}" in context
    assert "Latest OHLCV for AAPL: date=2026-07-03" in context
    assert "Fundamentals for AAPL: {pe=28.5, roe=0.21}" in context
    assert "Provider sentiment for AAPL: 0.730" in context
    assert "Sector for AAPL: Technology" in context
    assert "Next earnings for AAPL: 2026-07-30" in context
    assert "News for AAPL: raises guidance | buyback expanded" in context
    assert "Regime: label=neutral; vix=14.2" in context


def test_sparse_context_omits_missing_optional_evidence() -> None:
    graph = InMemoryGraphStore()
    item = intent(stop=None, target=None)
    orders = order_set(item)
    pm = linked_graph(graph, full=False)

    context = build_veto_context(graph, pm, orders, item)

    assert "stop_pct=n/a; target_pct=n/a" in context
    assert "sentiment_score=n/a" in context
    assert "suggested_stop_pct=n/a" in context
    assert "Scanner candidate for AAPL" not in context
    assert "Scanner verdict for AAPL" not in context
    assert "Latest OHLCV for AAPL" not in context
    assert "Fundamentals for AAPL" not in context
    assert "Regime:" not in context


def test_context_reports_missing_lineage() -> None:
    graph = InMemoryGraphStore()
    item = intent()
    orders = order_set(item)
    pm = graph.merge_node("PMRun", "pm", {})

    no_analyst = build_veto_context(graph, pm, orders, item)
    assert "Lineage: no AnalystRun linked to this PMRun." in no_analyst

    analyst = graph.merge_node("AnalystRun", "analyst", {"recommendation_set": recs()})
    graph.add_edge(analyst, pm, "EVALUATED_BY")
    no_scan = build_veto_context(graph, pm, orders, item)
    assert "Lineage: no ScanRun linked to this AnalystRun." in no_scan

    scan = graph.merge_node("ScanRun", "scan", {"candidate_set": candidates()})
    graph.add_edge(scan, analyst, "ANALYZED_BY")
    no_market = build_veto_context(graph, pm, orders, item)
    assert "Lineage: no MarketData linked to this ScanRun." in no_market

    graph = InMemoryGraphStore()
    market = graph.merge_node(
        "MarketData", "market", {"run_id": "market", "snapshot": market_data(True)}
    )
    scan = graph.merge_node("ScanRun", "scan", {"candidate_set": candidates()})
    graph.add_edge(scan, market, "DERIVED_FROM")
    analyst = graph.merge_node(
        "AnalystRun", "analyst", {"recommendation_set": recs(include_aapl=False)}
    )
    graph.add_edge(scan, analyst, "ANALYZED_BY")
    pm = graph.merge_node("PMRun", "pm", {})
    graph.add_edge(analyst, pm, "EVALUATED_BY")
    no_rec = build_veto_context(graph, pm, orders, item)
    assert "Analyst recommendation for AAPL" not in no_rec
