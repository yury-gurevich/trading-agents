"""Portfolio Manager rejected-order gate-report tests.

Agent: portfolio_manager
Role: prove rejected recommendations carry evaluated gate evidence.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.portfolio import PortfolioState
from agents.portfolio_manager.tests.helpers import (
    cash_portfolio,
    recommendation,
)
from contracts.common import Money

if TYPE_CHECKING:
    from contracts.portfolio_manager import GateOutcome, RejectedOrder


def test_2026_08_07_max_positions_rejection_keeps_cash_gate_failure() -> None:
    """PM-OUT-03 / PM-OBS-01 / PM-NEV-04: the 2026-08-07 MSFT rejection
    stays `max_positions` while proving `cash_available` failed too."""
    held = {f"HELD{i}": 1 for i in range(10)}
    values = {ticker: Money(amount=Decimal("20811.67")) for ticker in tuple(held)[:9]}
    values[tuple(held)[9]] = Money(amount=Decimal("20811.66"))
    portfolio = PortfolioState(
        cash=Money(amount=Decimal("103149.91")),
        positions=held,
        position_values=values,
        account_cash_cents=-10496677,
        account_equity_cents=10314991,
        account_buying_power_cents=16285963,
    )

    approved, rejected = evaluate_recommendations(
        (recommendation("MSFT"),),
        {"MSFT": Money(amount=Decimal("100.00"))},
        portfolio,
        max_position_pct=Decimal("0.10"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
    )

    gates = _gate_map(rejected[0])
    assert approved == ()
    assert rejected[0].reason == "max_positions"
    assert gates["max_positions"].passed is False
    assert gates["cash_available"].passed is False


def test_min_quantity_rejection_reports_only_position_gates() -> None:
    """PM-OUT-03 / PM-OBS-01: absent later gates are unknown, not passing."""
    approved, rejected = evaluate_recommendations(
        (recommendation("AAPL"),),
        {"AAPL": Money(amount=Decimal("100.00"))},
        cash_portfolio("10000.00"),
        max_position_pct=Decimal("0.01"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=2,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
    )

    assert approved == ()
    assert rejected[0].reason == "below_min_quantity"
    assert _gate_names(rejected[0]) == (
        "sizing",
        "min_order_quantity",
        "max_positions",
        "cash_available",
    )
    assert "reward_risk" not in _gate_names(rejected[0])


def test_reward_risk_rejection_carries_passing_position_gates() -> None:
    """PM-OUT-03 / PM-OBS-01 / PM-NEV-04: reward-risk rejects after position gates."""
    thin = recommendation("AAPL").model_copy(
        update={"suggested_stop_pct": 0.10, "suggested_target_pct": 0.10}
    )

    approved, rejected = evaluate_recommendations(
        (thin,),
        {"AAPL": Money(amount=Decimal("100.00"))},
        cash_portfolio("10000.00"),
        max_position_pct=Decimal("0.10"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
    )

    gates = _gate_map(rejected[0])
    assert approved == ()
    assert rejected[0].reason == "reward_risk_below_min"
    assert _gate_names(rejected[0]) == (
        "sizing",
        "min_order_quantity",
        "max_positions",
        "cash_available",
        "reward_risk",
    )
    assert all(gates[name].passed for name in tuple(gates)[:-1])
    assert gates["reward_risk"].passed is False


def test_sector_rejection_carries_every_prior_gate() -> None:
    """PM-OUT-03 / PM-OBS-01 / PM-NEV-06: sector rejection keeps prior gates."""
    approved, rejected = evaluate_recommendations(
        (recommendation("AAPL", 0.90), recommendation("MSFT", 0.80)),
        {
            "AAPL": Money(amount=Decimal("100.00")),
            "MSFT": Money(amount=Decimal("100.00")),
        },
        cash_portfolio("10000.00"),
        max_position_pct=Decimal("0.10"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
        sectors={"AAPL": "Technology", "MSFT": "Technology"},
        max_sector_pct=Decimal("1.00"),
        max_names_per_sector=1,
    )

    gates = _gate_map(rejected[0])
    assert [order.ticker for order in approved] == ["AAPL"]
    assert rejected[0].reason == "sector_name_count"
    assert _gate_names(rejected[0]) == (
        "sizing",
        "min_order_quantity",
        "max_positions",
        "cash_available",
        "reward_risk",
        "max_sector_pct",
        "max_names_per_sector",
    )
    assert gates["max_sector_pct"].passed is True
    assert gates["max_names_per_sector"].passed is False


def _gate_names(rejection: RejectedOrder) -> tuple[str, ...]:
    return tuple(gate.name for gate in rejection.gate_report)


def _gate_map(rejection: RejectedOrder) -> dict[str, GateOutcome]:
    return {gate.name: gate for gate in rejection.gate_report}
