"""Reward-risk invariants for volatility-scaled stop/target proposals.

Agent: portfolio_manager
Role: prove S150 does not turn the RR gate into a volatility filter.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from agents.portfolio_manager.domain.gate_report import stop_target_report
from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.tests.helpers import cash_portfolio, recommendation
from contracts.common import Money

if TYPE_CHECKING:
    from contracts.analyst import Recommendation
    from contracts.portfolio_manager import OrderIntent, RejectedOrder


def test_reward_risk_verdict_is_mode_invariant_when_both_values_scale() -> None:
    """PM-NEV-04 / PM-IDM-01: RR gate verdict is identical across modes."""
    flat = _item(stop_pct=0.05, target_pct=0.10)
    scaled = _item(stop_pct=0.08, target_pct=0.16)

    flat_report = stop_target_report(flat, 0.05, 0.10, 1.5)
    scaled_report = stop_target_report(scaled, 0.05, 0.10, 1.5)

    assert flat_report.outcome.value == scaled_report.outcome.value == 2.0
    assert flat_report.outcome.passed is scaled_report.outcome.passed is True


def test_volatile_scaled_name_still_passes_and_stop_only_scaling_fails() -> None:
    """PM-NEV-04 / PM-OBS-01: volatile names survive only if target scales too."""
    approved, rejected = _evaluate(_item(stop_pct=0.08, target_pct=0.16))
    bad_approved, bad_rejected = _evaluate(_item(stop_pct=0.08, target_pct=0.10))

    assert rejected == ()
    assert approved[0].ticker == "MRVL"
    assert bad_approved == ()
    assert bad_rejected[0].reason == "reward_risk_below_min"


def test_pm_default_stop_target_fallback_is_unchanged() -> None:
    """PM-OUT-02 / PM-NEV-04: absent recommendation stop uses PM defaults."""
    approved, rejected = _evaluate(recommendation("MRVL"))

    assert rejected == ()
    assert approved[0].stop_pct == 0.05
    assert approved[0].target_pct == 0.10


def test_reward_risk_threshold_still_rejects_poor_setups() -> None:
    """PM-NEV-04: genuinely poor RR remains rejected in both proposal modes."""
    flat_approved, flat_rejected = _evaluate(_item(stop_pct=0.05, target_pct=0.07))
    scaled_approved, scaled_rejected = _evaluate(_item(stop_pct=0.08, target_pct=0.112))

    assert flat_approved == ()
    assert scaled_approved == ()
    assert flat_rejected[0].reason == "reward_risk_below_min"
    assert scaled_rejected[0].reason == "reward_risk_below_min"


def _item(*, stop_pct: float, target_pct: float) -> Recommendation:
    return recommendation("MRVL").model_copy(
        update={"suggested_stop_pct": stop_pct, "suggested_target_pct": target_pct}
    )


def _evaluate(
    item: Recommendation,
) -> tuple[tuple[OrderIntent, ...], tuple[RejectedOrder, ...]]:
    return evaluate_recommendations(
        (item,),
        {"MRVL": Money(amount=Decimal("100.00"))},
        cash_portfolio("10000.00"),
        max_position_pct=Decimal("0.10"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
    )
