"""Reward-to-risk gate tests.

Agent: portfolio_manager
Role: verify the target_pct / stop_pct gate rejects thin or undefined setups.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.tests.helpers import cash_portfolio, recommendation
from contracts.common import Money

if TYPE_CHECKING:
    from contracts.portfolio_manager import OrderIntent, RejectedOrder


def _evaluate(
    stop_pct: float, target_pct: float, min_ratio: float = 1.5
) -> tuple[tuple[OrderIntent, ...], tuple[RejectedOrder, ...]]:
    item = recommendation("AAPL").model_copy(
        update={"suggested_stop_pct": stop_pct, "suggested_target_pct": target_pct}
    )
    return evaluate_recommendations(
        (item,),
        {"AAPL": Money(amount=Decimal("100.00"))},
        cash_portfolio("10000.00"),
        max_position_pct=Decimal("0.10"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=min_ratio,
    )


def test_rejects_when_reward_risk_below_minimum() -> None:
    """PM-NEV-04: min_reward_risk_ratio gate rejects thin R/R setups."""
    approved, rejected = _evaluate(stop_pct=0.10, target_pct=0.10)  # ratio 1.0 < 1.5

    assert approved == ()
    assert rejected[0].reason == "reward_risk_below_min"


def test_rejects_zero_stop_loss_as_undefined() -> None:
    approved, rejected = _evaluate(stop_pct=0.0, target_pct=0.10)

    assert approved == ()
    assert rejected[0].reason == "invalid_stop_loss"


def test_approves_when_ratio_meets_minimum() -> None:
    approved, rejected = _evaluate(stop_pct=0.05, target_pct=0.10)  # ratio 2.0 >= 1.5

    assert rejected == ()
    assert approved[0].ticker == "AAPL"
