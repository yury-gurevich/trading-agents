"""Portfolio Manager empty and exit rejected-report tests.

Agent: portfolio_manager
Role: prove rejected-order reports are empty only when no gates ran.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.result import reject_all
from agents.portfolio_manager.tests.helpers import (
    cash_portfolio,
    recommendation,
    recommendation_set,
)
from contracts.common import Money
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from contracts.portfolio_manager import GateOutcome, RejectedOrder


def test_precheck_rejection_carries_empty_gate_report() -> None:
    """PM-OUT-03 / PM-OBS-01: pre-gate rejections evaluated no gates."""
    hold = recommendation("AAPL").model_copy(update={"action": "hold"})

    approved, rejected = evaluate_recommendations(
        (hold,),
        {},
        cash_portfolio("10000.00"),
        max_position_pct=Decimal("0.10"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
    )

    assert approved == ()
    assert rejected[0].reason == "hold_recommendation"
    assert rejected[0].gate_report == ()


def test_reject_all_keeps_portfolio_level_report_empty() -> None:
    """PM-OUT-04 / PM-FAIL-01 / PM-OBS-02: provider-wide reject_all has no gates."""
    result = reject_all(
        InMemoryGraphStore(),
        recommendation_set=recommendation_set(recommendation("AAPL")),
        reason="provider_unavailable",
    )

    assert result.rejected[0].reason == "provider_unavailable"
    assert result.rejected[0].gate_report == ()


def test_sell_min_quantity_rejection_keeps_exit_gate_report() -> None:
    """PM-OUT-03 / PM-OBS-01 / PM-NEV-04: sell rejection carries exit gates."""
    sell = recommendation("AAPL").model_copy(update={"action": "sell"})

    approved, rejected = evaluate_recommendations(
        (sell,),
        {"AAPL": Money(amount=Decimal("25.00"))},
        cash_portfolio("10000.00", {"AAPL": 3}),
        max_position_pct=Decimal("0.10"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=5,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
    )

    gates = _gate_map(rejected[0])
    assert approved == ()
    assert rejected[0].reason == "below_min_quantity"
    assert _gate_names(rejected[0]) == (
        "sizing",
        "min_order_quantity",
        "max_positions",
        "cash_available",
    )
    assert gates["min_order_quantity"].passed is False
    assert gates["cash_available"].passed is True


def _gate_names(rejection: RejectedOrder) -> tuple[str, ...]:
    return tuple(gate.name for gate in rejection.gate_report)


def _gate_map(rejection: RejectedOrder) -> dict[str, GateOutcome]:
    return {gate.name: gate for gate in rejection.gate_report}
