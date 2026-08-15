"""Deliberation veto value-label tests.

Agent: orchestration
Role: verify debate-packet numbers carry unit/scope labels or explicit boundaries.
External I/O: none.
"""

from __future__ import annotations

from tests.veto_context_fixtures import intent, linked_graph, order_set

from kernel import InMemoryGraphStore
from orchestration.veto_context import build_veto_context


def test_full_context_names_available_value_units_and_boundaries() -> None:
    graph = InMemoryGraphStore()
    item = intent(stop=0.03, target=0.08)
    orders = order_set(item, refs=("pm-ref",))
    pm = linked_graph(graph, full=True)

    context = build_veto_context(graph, pm, orders, item)

    assert "PM order: action=buy; ticker=AAPL; quantity_shares=7" in context
    assert (
        "PM gate outcome: name=sizing value_portfolio_ratio=0.0812 "
        "threshold_portfolio_ratio=0.1 -> PASSED"
    ) in context
    assert "PM gate outcome: name=max_sector_pct" in context
    assert "deployed_this_batch_usd=0.00" in context
    assert "deployed=0.00" not in context
    assert "PM gate outcome: name=max_names_per_sector" in context
    assert "refs=['pm-ref']" in context
    assert "Analyst recommendation for AAPL" in context
    assert "analyst_sentiment_score=0.700" in context
    assert "fundamental_score=0.650" in context
    assert "Source-owned metric dictionaries:" in context
    assert "quant_metrics=source-owned-units-scope-unknown{composite_score=0.61" in (
        context
    )
    assert "history_bars=40" in context
    assert "relative_strength=0.08}" in context
    assert "Analyst rejected AAPL: duplicate exposure" in context
    assert "Scanner candidate for AAPL: rank_ordinal=1; scanner_score=0.810" in context
    assert "Scanner verdict for AAPL: decision=survived" in context
    assert "features=source-owned-units-scope-unknown{beta=1.1, return_5d=0.08}" in (
        context
    )
    assert "Latest OHLCV for AAPL: date=2026-07-03" in context
    assert "close_usd=116" in context
    assert "volume_shares=1500000" in context
    assert "Fundamentals for AAPL: source-owned-units-scope-unknown" in context
    assert "Provider sentiment for AAPL: provider_sentiment_score=0.730" in context
    assert "Sector for AAPL: Technology" in context
    assert "Next earnings for AAPL: 2026-07-30" in context
    assert "News for AAPL: raises guidance | buyback expanded" in context
    assert "Regime: label=neutral; vix_index=14.2" in context
    assert "Portfolio/batch context: unavailable" in context
    assert (
        "confidence_floor gate: confidence_score=0.620 vs "
        "base_min_confidence_score=0.570 -> PASSED"
    ) in context
    assert "stop_vs_regime_volatility gate:" in context
    assert "stop_pct=3.00% vs ATR%=" not in context
