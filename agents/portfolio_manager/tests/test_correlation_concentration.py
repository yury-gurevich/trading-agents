"""Correlated-cluster concentration tests.

Agent: portfolio_manager
Role: prove correlation caps use measured held-book clusters.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal

from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.tests.helpers import cash_portfolio
from agents.portfolio_manager.tests.s184_helpers import (
    SECTORS,
    buy,
    correlated_bars,
    gate,
)
from contracts.common import Money


def test_correlated_cluster_rejects_cross_label_order() -> None:
    """PM-NEV-08: measured correlation rejects a cross-label cluster."""
    portfolio = cash_portfolio(
        "10000.00",
        {"AAPL": 10, "MSFT": 10},
        position_values={
            "AAPL": Money(amount=Decimal("1000.00")),
            "MSFT": Money(amount=Decimal("1000.00")),
        },
    )

    approved, rejected = evaluate_recommendations(
        (buy("AMZN"),),
        {"AMZN": Money(amount=Decimal("100.00"))},
        portfolio,
        max_position_pct=Decimal("0.10"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
        sectors=SECTORS,
        max_sector_pct=Decimal("0.50"),
        max_names_per_sector=3,
        correlation_bars=correlated_bars(("AAPL", "MSFT", "AMZN"), days=66),
        correlation_lookback_days=120,
        correlation_threshold=0.70,
        max_correlated_cluster_pct=0.25,
        min_correlation_bars=60,
    )

    sector = gate(rejected[0], "max_sector_pct")
    names = gate(rejected[0], "max_names_per_sector")
    cluster = gate(rejected[0], "correlated_cluster_pct")
    assert approved == ()
    assert rejected[0].reason == "correlated_cluster_concentration"
    assert sector.outcome == "passed"
    assert names.outcome == "passed"
    assert cluster.outcome == "failed"
    assert cluster.value == 0.30
    assert "cluster_issuers=AAPL,AMZN,MSFT" in cluster.detail


def test_short_correlation_history_is_not_evaluated() -> None:
    """PM-NEV-09: too few overlapping bars emits NOT-EVALUATED, never a pass."""
    portfolio = cash_portfolio(
        "10000.00",
        {"AAPL": 10},
        position_values={"AAPL": Money(amount=Decimal("1000.00"))},
    )

    approved, rejected = evaluate_recommendations(
        (buy("MSFT"),),
        {"MSFT": Money(amount=Decimal("100.00"))},
        portfolio,
        max_position_pct=Decimal("0.10"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
        sectors=SECTORS,
        max_sector_pct=Decimal("0.50"),
        max_names_per_sector=3,
        correlation_bars=correlated_bars(("AAPL", "MSFT"), days=10),
        correlation_lookback_days=120,
        correlation_threshold=0.70,
        max_correlated_cluster_pct=0.25,
        min_correlation_bars=60,
    )

    cluster = gate(rejected[0], "correlated_cluster_pct")
    assert approved == ()
    assert rejected[0].reason == "correlation_not_evaluated"
    assert cluster.outcome == "not_evaluated"
    assert "missing_input=overlapping_return_bars" in cluster.detail
