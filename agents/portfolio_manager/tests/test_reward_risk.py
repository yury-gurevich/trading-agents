"""Reward-to-risk gate tests.

Agent: portfolio_manager
Role: verify the target_pct / stop_pct gate rejects thin or undefined setups.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from agents.portfolio_manager.domain.gate_report import stop_target_report
from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.tests.helpers import cash_portfolio, recommendation
from contracts.analyst import StopTargetEvidence
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


def test_a_structurally_fixed_gate_discloses_that_it_could_not_differ() -> None:
    """PM-OBS-04: a fixed reward/risk verdict says the other answer was unreachable."""
    item = recommendation("AAPL").model_copy(
        update={
            "suggested_stop_pct": 0.08,
            "suggested_target_pct": 0.16,
            "stop_target_evidence": StopTargetEvidence(
                mode="scaled",
                counterfactual_mode="flat",
                atr_pct=0.064,
                volatility_present=True,
                volatility_fallback=False,
                applied_stop_pct=0.08,
                applied_target_pct=0.16,
                counterfactual_stop_pct=0.05,
                counterfactual_target_pct=0.10,
                flat_stop_pct=0.05,
                flat_target_pct=0.10,
                scaled_stop_pct=0.08,
                scaled_target_pct=0.16,
            ),
        }
    )

    report = stop_target_report(item, 0.05, 0.10, 1.5)

    assert report.outcome.outcome == "passed"
    assert "base_stop_loss_pct=0.0500" in report.outcome.detail
    assert "base_take_profit_pct=0.1000" in report.outcome.detail
    assert "applied_mode=scaled" in report.outcome.detail
    assert "comparison=STRUCTURALLY_DETERMINED" in report.outcome.detail


def test_a_zero_stop_ratio_is_not_labelled_structurally_fixed() -> None:
    """PM-OBS-04 / PM-NEV-04: invalid stops are validity failures, not policy."""
    item = recommendation("AAPL").model_copy(
        update={
            "suggested_stop_pct": 0.0,
            "suggested_target_pct": 0.10,
            "stop_target_evidence": StopTargetEvidence(
                mode="scaled",
                counterfactual_mode="flat",
                atr_pct=0.0,
                volatility_present=True,
                volatility_fallback=False,
                applied_stop_pct=0.0,
                applied_target_pct=0.10,
                counterfactual_stop_pct=0.0,
                counterfactual_target_pct=0.10,
                flat_stop_pct=0.0,
                flat_target_pct=0.10,
                scaled_stop_pct=0.0,
                scaled_target_pct=0.10,
            ),
        }
    )

    report = stop_target_report(item, 0.0, 0.10, 0.0)

    assert report.outcome.outcome == "failed"
    assert "base_stop_loss_pct=0.0000" in report.outcome.detail
    assert "comparison=INFORMATIVE" in report.outcome.detail
    assert "comparison=DISCLOSURE_ONLY" not in report.outcome.detail


def test_rejects_zero_stop_loss_as_undefined() -> None:
    """PM-NEV-04: floor 0 does not approve a non-positive stop."""
    approved, rejected = _evaluate(stop_pct=0.0, target_pct=0.10, min_ratio=0.0)

    assert approved == ()
    assert rejected[0].reason == "invalid_stop_loss"
    assert rejected[0].gate_report[-1].threshold == 0.0
    assert "comparison=DISCLOSURE_ONLY" not in rejected[0].gate_report[-1].detail


def test_approves_when_ratio_meets_minimum() -> None:
    approved, rejected = _evaluate(stop_pct=0.05, target_pct=0.10)  # ratio 2.0 >= 1.5

    assert rejected == ()
    assert approved[0].ticker == "AAPL"


def test_reward_risk_gate_holds_ratio_boundary() -> None:
    """Kills
    agents.portfolio_manager.domain.gate_report.x_stop_target_report__mutmut_11.
    """
    below = _evaluate(stop_pct=0.125, target_pct=0.1874)
    at = _evaluate(stop_pct=0.125, target_pct=0.1875)
    above = _evaluate(stop_pct=0.125, target_pct=0.1876)

    assert below[0] == ()
    assert below[1][0].reason == "reward_risk_below_min"
    assert at[1] == ()
    assert at[0][0].ticker == "AAPL"
    assert above[1] == ()
    assert above[0][0].ticker == "AAPL"


def test_reward_risk_gate_holds_nonpositive_stop_boundary() -> None:
    """Kills
    agents.portfolio_manager.domain.gate_report.x_stop_target_report__mutmut_6.
    """
    item = recommendation("AAPL").model_copy(
        update={"suggested_stop_pct": 0.0, "suggested_target_pct": 0.10}
    )

    report = stop_target_report(item, 0.05, 0.10, 0.0)

    assert report.stop_pct == 0.0
    assert report.target_pct == 0.10
    assert report.outcome.value == 0.0
    assert report.outcome.threshold == 0.0
    assert report.outcome.passed is False
