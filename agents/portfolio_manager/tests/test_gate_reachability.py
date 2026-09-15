"""Portfolio Manager gate-reachability disclosure tests.

Agent: portfolio_manager
Role: verify gate reports distinguish fixed policy comparisons from live evidence.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal

from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.tests.helpers import cash_portfolio, recommendation
from agents.portfolio_manager.tests.s184_helpers import correlated_bars
from contracts.common import Money


def test_a_gate_whose_value_varies_is_not_marked_structurally_fixed() -> None:
    """PM-OBS-04: full gate reports distinguish fixed from data-varying gates."""
    approved, rejected = evaluate_recommendations(
        (recommendation("AAPL"),),
        {"AAPL": Money(amount=Decimal("100.00"))},
        cash_portfolio(
            "10000.00",
            {"MSFT": 1},
            position_values={"MSFT": Money(amount=Decimal("100.00"))},
        ),
        max_position_pct=Decimal("0.10"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
        sectors={"AAPL": "Technology", "MSFT": "Software"},
        max_sector_pct=Decimal("0.30"),
        max_names_per_sector=3,
        correlation_bars=correlated_bars(("AAPL", "MSFT"), days=66),
        correlation_lookback_days=120,
        correlation_threshold=0.70,
        max_correlated_cluster_pct=0.25,
        min_correlation_bars=60,
    )

    gates = {gate.name: gate for gate in approved[0].gate_report}
    structurally_fixed = {
        name
        for name, gate in gates.items()
        if "comparison=STRUCTURALLY_DETERMINED" in gate.detail
    }

    assert rejected == ()
    assert {
        "sizing",
        "min_order_quantity",
        "max_positions",
        "cash_available",
        "reward_risk",
        "max_sector_pct",
        "max_names_per_sector",
        "correlated_cluster_pct",
    } <= gates.keys()
    assert structurally_fixed == {"reward_risk"}
