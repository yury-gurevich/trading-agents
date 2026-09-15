"""Correlated-cluster concentration tests.

Agent: portfolio_manager
Role: prove correlation caps use measured held-book clusters.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.tests.helpers import cash_portfolio
from agents.portfolio_manager.tests.s184_helpers import (
    SECTORS,
    buy,
    correlated_bars,
    gate,
)
from contracts.common import Money

if TYPE_CHECKING:
    from contracts.provider import OHLCVBar


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


def test_one_unusable_pair_does_not_disable_the_whole_gate() -> None:
    """PM-OBS-04 / PM-NEV-09: one thin pair is skipped, not a gate-wide abort."""
    portfolio = cash_portfolio(
        "10000.00",
        {"AAPL": 10, "MSFT": 10},
        position_values={
            "AAPL": Money(amount=Decimal("500.00")),
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
        correlation_bars=_one_short_pair_bars(),
        correlation_lookback_days=120,
        correlation_threshold=0.70,
        max_correlated_cluster_pct=0.15,
        min_correlation_bars=60,
    )

    cluster = gate(rejected[0], "correlated_cluster_pct")
    assert approved == ()
    assert rejected[0].reason == "correlated_cluster_concentration"
    assert cluster.outcome == "failed"
    assert "cluster_issuers=AMZN,MSFT" in cluster.detail
    assert "skipped_pairs=1" in cluster.detail


def test_every_pair_unusable_still_reports_not_evaluated() -> None:
    """PM-NEV-09 / PM-OBS-04: no usable pair remains NOT-EVALUATED, never passed."""
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
    assert "skipped_pairs=1" in cluster.detail
    assert "skipped_pair_issuers=AAPL:9" in cluster.detail


def _one_short_pair_bars() -> tuple[OHLCVBar, ...]:
    return (
        *correlated_bars(("AAPL",), days=10),
        *correlated_bars(("MSFT", "AMZN"), days=66),
    )
