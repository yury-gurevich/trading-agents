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

from contracts.analyst import Recommendation
from contracts.common import Explanation, Money, Window
from contracts.portfolio_manager import GateOutcome, OrderIntent
from contracts.researcher import (
    CONTRACT,
    BacktestEvidence,
    FactorProposal,
    ParameterChangeProposal,
    ProposedFactor,
)


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
        passed=True,
        detail="fixture",
    )
    current = legacy.model_copy(update={"gate_report": (outcome,)})

    parsed = OrderIntent.model_validate(current.model_dump(mode="json"))

    assert legacy.gate_report == ()
    assert parsed.gate_report == (outcome,)


def test_researcher_backtest_evidence_round_trips_optionally() -> None:
    evidence = BacktestEvidence(
        sharpe=1.2,
        ic_mean=0.03,
        max_drawdown=-0.10,
        turnover=0.25,
        n_days=120,
        window_start="2024-01-01",
        window_end="2024-06-30",
        holdout_sharpe=0.8,
        holdout_ic_mean=0.02,
        slippage_bps=10.0,
    )
    proposal = ParameterChangeProposal(
        proposal_id="bt",
        changes=(),
        rationale=Explanation(summary="fixture"),
        provenance={"run_id": "bt", "source_agent": "researcher"},
        backtest=evidence,
    )

    parsed = ParameterChangeProposal.model_validate(proposal.model_dump(mode="json"))

    assert CONTRACT.version == "0.3.0"
    assert parsed.backtest == evidence


def test_researcher_factor_proposal_round_trips_optionally() -> None:
    evidence = BacktestEvidence(
        sharpe=1.2,
        ic_mean=0.03,
        max_drawdown=-0.10,
        turnover=0.25,
        n_days=120,
        window_start="2024-01-01",
        window_end="2024-06-30",
        holdout_sharpe=0.8,
        holdout_ic_mean=0.02,
        slippage_bps=10.0,
    )
    proposal = FactorProposal(
        proposal_id="factor",
        factor=ProposedFactor(
            name="momentum",
            params=(("lookback", 20.0),),
            rationale=Explanation(summary="bounded catalogue member"),
        ),
        provenance={"run_id": "factor", "source_agent": "researcher"},
        backtest=evidence,
    )

    parsed = FactorProposal.model_validate(proposal.model_dump(mode="json"))

    assert parsed.factor.params == (("lookback", 20.0),)
    assert parsed.backtest == evidence
