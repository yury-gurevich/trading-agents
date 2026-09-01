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
    order_set,
    recs,
)
from tests.veto_context_provider_fixtures import market_data, regime

from contracts.analyst import RecommendationSet
from contracts.portfolio_manager import GateOutcome, GateStatus
from contracts.provider import MarketData, RegimeContext
from kernel import InMemoryGraphStore
from orchestration.veto_context import build_veto_context
from orchestration.veto_context_pm import regime_gate_lines


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
        outcome=GateStatus.FAILED,
        detail="sector=Technology",
    )
    item = intent(stop=0.05, target=0.04, gates=(failed,))
    orders = order_set(item)
    pm = linked_graph(graph, full=True)

    context = build_veto_context(graph, pm, orders, item)

    assert (
        "name=max_sector_pct value_sector_exposure_ratio=0.41 "
        "threshold_sector_exposure_ratio=0.3 -> FAILED"
    ) in context
    assert "base_stop_loss_pct=3.00% -> FAILED" in context
    assert "base_take_profit_pct=8.00% -> FAILED" in context


def test_context_renders_not_evaluated_gate_outcomes_plainly() -> None:
    """PM-NEV-09: PM context carries NOT-EVALUATED without treating it as pass."""
    graph = InMemoryGraphStore()
    not_evaluated = GateOutcome(
        name="correlated_cluster_pct",
        value=0.0,
        threshold=0.25,
        outcome=GateStatus.NOT_EVALUATED,
        detail="missing_input=overlapping_return_bars",
    )
    item = intent(gates=(not_evaluated,))
    orders = order_set(item)
    pm = linked_graph(graph, full=True)

    context = build_veto_context(graph, pm, orders, item)

    assert (
        "name=correlated_cluster_pct value_cluster_exposure_ratio=0 "
        "threshold_cluster_exposure_ratio=0.25 -> NOT-EVALUATED"
    ) in context
    assert "missing_input=overlapping_return_bars" in context


def test_regime_context_does_not_invent_an_atr_gate_outcome() -> None:
    """DLIB-NEV-06 / DL-104: PM context may not fabricate a gate verdict."""
    item = intent()
    rec = RecommendationSet.model_validate(recs()).recommendations[0]
    market = MarketData.model_validate(market_data(full=False))
    regime_context = RegimeContext.model_validate(regime())

    stop_line = regime_gate_lines(regime_context, rec, item, market.bars)[2]

    assert "stop_vs_regime_volatility gate:" in stop_line
    assert "ATR%" not in stop_line
    assert "stop_pct=3.00% vs base_stop_loss_pct=3.00%" in stop_line


def test_context_renders_stop_target_basis_from_analyst_evidence() -> None:
    """ANLZ-OBS-03 / DL-113: stop proposal names mode and ATR availability."""
    graph = InMemoryGraphStore()
    item = intent(stop=0.03, target=0.08)
    orders = order_set(item)
    pm = linked_graph(graph, full=True)

    context = build_veto_context(graph, pm, orders, item)

    assert (
        "stop_target basis: mode=flat; volatility_present=True; "
        "volatility_fallback=False; atr_pct=2.94%; "
        "applied_stop_pct=3.00%; applied_target_pct=8.00%; "
        "counterfactual_mode=scaled"
    ) in context


def test_sparse_context_omits_missing_optional_evidence() -> None:
    graph = InMemoryGraphStore()
    item = intent(stop=None, target=None, gates=())
    orders = order_set(item)
    pm = linked_graph(graph, full=False)

    context = build_veto_context(graph, pm, orders, item)

    assert "stop_pct=n/a; target_pct=n/a" in context
    assert "PM gate report unavailable" in context
    assert "analyst_sentiment_score=n/a" in context
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
