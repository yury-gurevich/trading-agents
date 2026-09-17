"""Reward-risk gate tests for measured analyst target evidence.

Agent: portfolio_manager
Role: prove reward_risk consumes analyst measured-upside targets, not constants.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from agents.analyst.domain.recommend import decide
from agents.analyst.domain.scoring import score_candidate
from agents.analyst.settings import AnalystSettings
from agents.analyst.tests.helpers import candidate
from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.portfolio import PortfolioState
from agents.portfolio_manager.settings import PortfolioManagerSettings
from contracts.common import Money, Provenance
from contracts.provider import OHLCVBar, RegimeContext

if TYPE_CHECKING:
    from contracts.analyst import Recommendation
    from contracts.portfolio_manager import GateOutcome, OrderIntent, RejectedOrder


def test_reward_risk_varies_across_measured_excursion_profiles() -> None:
    """ANLZ-OBS-06 / PM-OBS-05: reward_risk varies with measured upside."""
    first = _recommendation_from_profile("AAPL", high_after_anchor=130.0)
    second = _recommendation_from_profile("MSFT", high_after_anchor=160.0)

    approved, rejected = _evaluate(first, second, min_ratio=0.80)
    gates = {
        intent.ticker: _gate(intent.gate_report, "reward_risk") for intent in approved
    }

    assert rejected == ()
    assert gates["AAPL"].value != gates["MSFT"].value
    assert {gates["AAPL"].value, gates["MSFT"].value} != {2.0}


def test_default_reward_risk_floor_is_the_corrected_built_ratio_floor() -> None:
    """PM-NEV-04: ADR-0027 Correction / EXP-010 set the built-ratio floor."""
    assert PortfolioManagerSettings().min_reward_risk_ratio == 0.80


def test_reward_risk_rejects_measured_upside_below_default_floor() -> None:
    """ANLZ-TYP-02 / ANLZ-OBS-06 / PM-OBS-05 / PM-NEV-04: floor still binds."""
    poor = _recommendation_from_profile("AAPL", high_after_anchor=103.0)

    approved, rejected = _evaluate(poor, min_ratio=0.80)
    gate = _gate(rejected[0].gate_report, "reward_risk")

    assert approved == ()
    assert rejected[0].reason == "reward_risk_below_min"
    assert gate.threshold == 0.80
    assert gate.value < 0.80


def test_reward_risk_between_old_and_new_floor_passes_by_default() -> None:
    """PM-NEV-04 / PM-OBS-05: 0.80 recalibration is behavioral, not cosmetic."""
    item = _recommendation_from_profile("AAPL", high_after_anchor=104.5)
    default_floor = PortfolioManagerSettings().min_reward_risk_ratio

    approved, rejected = _evaluate(item, min_ratio=default_floor)
    gate = _gate(approved[0].gate_report, "reward_risk")

    assert rejected == ()
    assert approved[0].ticker == "AAPL"
    assert gate.threshold == 0.80
    assert 0.80 <= gate.value < 1.0


def test_measured_reward_risk_is_not_labelled_structurally_fixed() -> None:
    """PM-OBS-04 / PM-OBS-05: measured target evidence is informative."""
    item = _recommendation_from_profile("AAPL", high_after_anchor=130.0)

    approved, rejected = _evaluate(item, min_ratio=0.80)
    gate = _gate(approved[0].gate_report, "reward_risk")

    assert rejected == ()
    assert "target_basis=trailing_favorable_excursion" in gate.detail
    assert "favorable_excursion_sample_count=5" in gate.detail
    assert "comparison=INFORMATIVE" in gate.detail
    assert "comparison=STRUCTURALLY_DETERMINED" not in gate.detail


def test_reward_risk_floor_is_read_from_the_tunable_value() -> None:
    """PM-NEV-04: changing min_reward_risk_ratio changes the reward-risk verdict."""
    item = _recommendation_from_profile("AAPL", high_after_anchor=106.0)

    approved, rejected = _evaluate(item, min_ratio=1.0)
    strict_approved, strict_rejected = _evaluate(item, min_ratio=2.0)

    assert rejected == ()
    assert approved[0].ticker == "AAPL"
    assert strict_approved == ()
    assert strict_rejected[0].reason == "reward_risk_below_min"
    assert _gate(strict_rejected[0].gate_report, "reward_risk").threshold == 2.0


def _recommendation_from_profile(
    ticker: str, *, high_after_anchor: float
) -> Recommendation:
    settings = AnalystSettings(stop_target_mode="flat")
    score = score_candidate(
        candidate(ticker),
        _bars(ticker, high_after_anchor=high_after_anchor),
        {},
        (),
        (),
        settings,
    )
    decision = decide(candidate(ticker), score, _regime(), settings=settings)
    assert decision.recommendation is not None
    return decision.recommendation


def _evaluate(
    *recommendations: Recommendation, min_ratio: float
) -> tuple[tuple[OrderIntent, ...], tuple[RejectedOrder, ...]]:
    prices = {item.ticker: Money(amount=Decimal("100.00")) for item in recommendations}
    return evaluate_recommendations(
        tuple(recommendations),
        prices,
        PortfolioState(
            cash=Money(amount=Decimal("100000.00")),
            positions={},
            position_values={},
        ),
        max_position_pct=Decimal("0.01"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=min_ratio,
    )


def _gate(gates: tuple[GateOutcome, ...], name: str) -> GateOutcome:
    for gate in gates:
        if gate.name == name:
            return gate
    raise AssertionError(f"missing gate {name!r}")


def _bars(ticker: str, *, high_after_anchor: float) -> tuple[OHLCVBar, ...]:
    start = date(2025, 1, 1)
    rows = []
    for offset in range(15):
        high = high_after_anchor if offset > 4 else 100.0
        rows.append(
            OHLCVBar(
                ticker=ticker,
                bar_date=start + timedelta(days=offset),
                open=100.0,
                high=high,
                low=95.0,
                close=100.0,
                volume=1_000_000,
            )
        )
    return tuple(rows)


def _regime() -> RegimeContext:
    return RegimeContext(
        label="risk_on",
        vix=12.0,
        as_of=datetime.now(tz=UTC),
        base_min_confidence=0.0,
        base_stop_loss_pct=0.05,
        base_take_profit_pct=0.10,
        base_max_holding_days=10,
        provenance=Provenance(run_id="regime-fixture", source_agent="provider"),
    )
