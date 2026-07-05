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
    regime,
)

from contracts.analyst import RecommendationSet
from contracts.portfolio_manager import GateOutcome
from contracts.provider import MarketData, RegimeContext
from kernel import InMemoryGraphStore
from orchestration.veto_context import build_veto_context
from orchestration.veto_context_pm import regime_gate_lines


def test_full_context_includes_all_available_upstream_evidence() -> None:
    graph = InMemoryGraphStore()
    item = intent(stop=0.03, target=0.08)
    orders = order_set(item, refs=("pm-ref",))
    pm = linked_graph(graph, full=True)

    context = build_veto_context(graph, pm, orders, item)

    assert "PM order: action=buy; ticker=AAPL; quantity=7" in context
    assert (
        "PM gate outcome: name=sizing value=0.0812 threshold=0.1 -> PASSED"
    ) in context
    assert "PM gate outcome: name=max_sector_pct" in context
    assert "PM gate outcome: name=max_names_per_sector" in context
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
    assert (
        "confidence_floor gate: confidence=0.620 vs base_min_confidence=0.570 -> PASSED"
    ) in context
    assert "stop_vs_regime_volatility gate:" in context
    assert "stop_pct=3.00% vs ATR%=" in context


def test_context_completeness_renders_every_enforced_gate_with_outcome() -> None:
    graph = InMemoryGraphStore()
    item = intent(stop=0.03, target=0.08)
    orders = order_set(item)
    pm = linked_graph(graph, full=True)

    context = build_veto_context(graph, pm, orders, item)

    required = (
        "name=sizing",
        "name=max_sector_pct",
        "name=max_names_per_sector",
        "confidence_floor gate",
        "stop_vs_regime_volatility gate",
    )
    for gate in required:
        line = next(line for line in context.splitlines() if gate in line)
        assert "PASSED" in line or "FAILED" in line


def test_context_renders_failed_gate_outcomes_plainly() -> None:
    graph = InMemoryGraphStore()
    failed = GateOutcome(
        name="max_sector_pct",
        value=0.41,
        threshold=0.30,
        passed=False,
        detail="sector=Technology",
    )
    item = intent(stop=0.05, target=0.04, gates=(failed,))
    orders = order_set(item)
    pm = linked_graph(graph, full=True)

    context = build_veto_context(graph, pm, orders, item)

    assert "name=max_sector_pct value=0.41 threshold=0.3 -> FAILED" in context
    assert "base_stop_loss_pct=3.00% -> FAILED" in context
    assert "base_take_profit_pct=8.00% -> FAILED" in context


def test_regime_present_without_ticker_atr_is_reported_plainly() -> None:
    item = intent()
    rec = RecommendationSet.model_validate(recs()).recommendations[0]
    market = MarketData.model_validate(market_data(full=False))
    regime_context = RegimeContext.model_validate(regime())

    stop_line = regime_gate_lines(regime_context, rec, item, market.bars)[2]

    assert "ATR%=unavailable (need at least 2 OHLCV bars)" in stop_line


def test_sparse_context_omits_missing_optional_evidence() -> None:
    graph = InMemoryGraphStore()
    item = intent(stop=None, target=None, gates=())
    orders = order_set(item)
    pm = linked_graph(graph, full=False)

    context = build_veto_context(graph, pm, orders, item)

    assert "stop_pct=n/a; target_pct=n/a" in context
    assert "PM gate report unavailable" in context
    assert "sentiment_score=n/a" in context
    assert "suggested_stop_pct=n/a" in context
    assert "Scanner candidate for AAPL" not in context
    assert "Scanner verdict for AAPL" not in context
    assert "Latest OHLCV for AAPL" not in context
    assert "Fundamentals for AAPL" not in context
    assert "Regime: unavailable" in context
    assert "confidence_floor gate unavailable" in context
    assert "stop_vs_regime_volatility gate unavailable" in context


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
