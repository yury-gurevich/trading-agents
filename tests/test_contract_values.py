"""Contract value validation tests.

Agent: contracts (shared)
Role: verify invalid payload values fail at typed message boundaries.
External I/O: none.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from contracts.analyst import CONTRACT as ANALYST_CONTRACT
from contracts.analyst import QuantMetric, Recommendation
from contracts.common import Explanation, Money, Window
from contracts.execution import CONTRACT as EXECUTION_CONTRACT
from contracts.portfolio_manager import GateOutcome, GateStatus, OrderIntent


def test_money_rejects_negative_amount() -> None:
    with pytest.raises(ValidationError):
        Money(amount=Decimal("-0.01"))


def test_window_rejects_start_after_end() -> None:
    with pytest.raises(ValidationError, match="start must be on or before end"):
        Window(start=date(2026, 1, 2), end=date(2026, 1, 1))


def test_recommendation_rejects_confidence_above_one() -> None:
    with pytest.raises(ValidationError):
        Recommendation(
            ticker="AAPL",
            action="buy",
            confidence=1.01,
            technical_score=0.5,
            rationale=Explanation(summary="fixture"),
        )


def test_recommendation_quant_metrics_are_typed_and_bounded() -> None:
    rec = Recommendation(
        ticker="AAPL",
        action="buy",
        confidence=0.8,
        technical_score=0.5,
        quant_metrics=(QuantMetric(name="composite_score", value=0.61),),
        rationale=Explanation(summary="fixture"),
    )

    assert rec.quant_metrics[0].name == "composite_score"
    with pytest.raises(ValidationError):
        QuantMetric(name="", value=0.0)


def test_recommendation_exit_trigger_is_optional_and_bounded() -> None:
    rec = Recommendation(
        ticker="AAPL",
        action="sell",
        exit_trigger="stop",
        confidence=0.8,
        technical_score=0.5,
        rationale=Explanation(summary="fixture"),
    )

    assert rec.exit_trigger == "stop"
    with pytest.raises(ValidationError):
        Recommendation.model_validate(
            {
                "ticker": "AAPL",
                "action": "sell",
                "exit_trigger": "target",
                "confidence": 0.8,
                "technical_score": 0.5,
                "rationale": {"summary": "fixture"},
            }
        )


def test_order_intent_rejects_zero_quantity() -> None:
    with pytest.raises(ValidationError):
        OrderIntent(
            ticker="AAPL",
            action="buy",
            quantity=0,
            est_price=Money(amount=Decimal("100.00")),
            rationale=Explanation(summary="fixture"),
        )


def test_order_intent_gate_report_is_additive_and_round_trips() -> None:
    legacy = OrderIntent(
        ticker="AAPL",
        action="buy",
        quantity=1,
        est_price=Money(amount=Decimal("100.00")),
        rationale=Explanation(summary="fixture"),
    )
    outcome = GateOutcome(
        name="sizing",
        value=0.10,
        threshold=0.10,
        outcome=GateStatus.PASSED,
        detail="fixture",
    )
    current = legacy.model_copy(update={"gate_report": (outcome,)})

    parsed = OrderIntent.model_validate(current.model_dump(mode="json"))

    assert legacy.gate_report == ()
    assert parsed.gate_report == (outcome,)


def test_gate_outcome_has_three_wire_states_and_legacy_passed_view() -> None:
    """PM-TYP-03: GateOutcome carries passed, failed, and not-evaluated."""
    historical = GateOutcome.model_validate(
        {
            "name": "sizing",
            "value": 0.10,
            "threshold": 0.10,
            "passed": True,
            "detail": "historical",
        }
    )
    blocked = GateOutcome.model_validate(
        {
            "name": "sizing",
            "value": 0.11,
            "threshold": 0.10,
            "passed": False,
            "detail": "historical",
        }
    )
    string_passed = GateOutcome.model_validate(
        {
            "name": "sizing",
            "value": 0.10,
            "threshold": 0.10,
            "passed": "passed",
            "detail": "historical",
        }
    )
    not_evaluated = GateOutcome(
        name="correlated_cluster_pct",
        value=0.0,
        threshold=0.25,
        outcome=GateStatus.NOT_EVALUATED,
        detail="missing_input=overlapping_return_bars",
    )

    dumped = not_evaluated.model_dump(mode="json")

    assert historical.outcome == GateStatus.PASSED
    assert historical.passed is True
    assert blocked.outcome == GateStatus.FAILED
    assert blocked.passed is False
    assert string_passed.outcome == GateStatus.PASSED
    assert dumped["outcome"] == "not_evaluated"
    assert "passed" not in dumped
    # PM-NEV-09: a boolean cannot carry "not evaluated", so asking for one is a
    # question with no honest answer. Returning False would report a breach the
    # gate never looked for.
    with pytest.raises(ValueError, match="was not evaluated"):
        _ = not_evaluated.passed


def test_broker_native_stops_bump_contract_ownership() -> None:
    assert EXECUTION_CONTRACT.version == "0.3.1"
    assert "BrokerStopOrder" in EXECUTION_CONTRACT.owns_graph
    assert ANALYST_CONTRACT.version == "0.5.0"
