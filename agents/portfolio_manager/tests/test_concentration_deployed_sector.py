"""Sector concentration denominator migration tests.

Agent: portfolio_manager
Role: prove sector concentration divides by deployed capital while sizing does not.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

import pytest

from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.domain.sector_gate_outcomes import sector_exposure_outcome
from agents.portfolio_manager.tests.helpers import cash_portfolio
from agents.portfolio_manager.tests.s184_helpers import buy
from contracts.common import Money
from contracts.portfolio_manager import GateStatus

if TYPE_CHECKING:
    from contracts.portfolio_manager import GateOutcome, OrderIntent

_EQUITY = Decimal("102208.78")
_DEPLOYED = Decimal("21711.95")
_WFC_COST = Decimal("986.86")
_BANKING_HELD_FOR_RECORDED_RATIO = Decimal("2927.80")


def test_sector_gate_uses_deployed_book_denominator() -> None:
    """PM-NEV-06 / PM-NEV-09: max_sector_pct measures deployed book concentration."""
    approved, rejected = evaluate_recommendations(
        (buy("WFC"),),
        {"WFC": Money(amount=_WFC_COST)},
        cash_portfolio(
            str(_EQUITY),
            {"JPM": 1, "OTHER": 1},
            position_values={
                "JPM": Money(amount=_BANKING_HELD_FOR_RECORDED_RATIO),
                "OTHER": Money(amount=_DEPLOYED - _BANKING_HELD_FOR_RECORDED_RATIO),
            },
        ),
        max_position_pct=Decimal("0.01"),
        max_positions=60,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
        sectors={"JPM": "Banking", "OTHER": "Other", "WFC": "Banking"},
        max_sector_pct=Decimal("0.30"),
        max_names_per_sector=3,
    )

    sector = _approved_gate(approved, "max_sector_pct")
    assert rejected == ()
    assert sector.outcome == "passed"
    assert sector.value == pytest.approx(0.1803, abs=0.0001)
    assert "denominator=deployed_capital" in sector.detail


@pytest.mark.parametrize("deployed", [Decimal("0"), Decimal("9000.00")])
def test_below_derived_sector_floor_is_not_evaluated(deployed: Decimal) -> None:
    """PM-NEV-09: below the derived deployment floor is NOT_EVALUATED, never failed."""
    positions = {} if deployed == 0 else {"AAPL": 1}
    position_values = {} if deployed == 0 else {"AAPL": Money(amount=deployed)}

    approved, rejected = evaluate_recommendations(
        (buy("WFC"),),
        {"WFC": Money(amount=_WFC_COST)},
        cash_portfolio(str(_EQUITY), positions, position_values=position_values),
        max_position_pct=Decimal("0.01"),
        max_positions=60,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
        sectors={"AAPL": "Technology", "WFC": "Banking"},
        max_sector_pct=Decimal("0.30"),
        max_names_per_sector=3,
    )

    sector = _approved_gate(approved, "max_sector_pct")
    assert rejected == ()
    assert sector.outcome == "not_evaluated"
    assert sector.outcome != "failed"
    assert "reason=deployment_below_floor" in sector.detail
    assert "deployment_floor_pct=0.1000" in sector.detail
    assert f"deployed_portfolio_usd={deployed:.2f}" in sector.detail


def test_sizing_still_uses_equity_denominator() -> None:
    """PM-NEV-04: sizing stays on equity while concentration moves."""
    approved, rejected = evaluate_recommendations(
        (buy("AMZN"),),
        {"AMZN": Money(amount=Decimal("993.77"))},
        cash_portfolio(
            str(_EQUITY),
            {"OTHER": 1},
            position_values={"OTHER": Money(amount=_DEPLOYED)},
        ),
        max_position_pct=Decimal("0.01"),
        max_positions=60,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
        sectors={"OTHER": "Other", "AMZN": "Retail"},
        max_sector_pct=Decimal("1.00"),
        max_names_per_sector=0,
    )

    sizing = _approved_gate(approved, "sizing")
    assert rejected == ()
    assert sizing.outcome == "passed"
    assert sizing.value == pytest.approx(0.009723, abs=0.000001)
    assert "portfolio_value_usd=102208.78" in sizing.detail


@pytest.mark.parametrize(
    ("names_cap", "sector_cap", "expected_floor"),
    [(4, Decimal("0.30"), "0.1333"), (3, Decimal("0.20"), "0.1500")],
)
def test_floor_is_derived_from_live_tunables(
    names_cap: int, sector_cap: Decimal, expected_floor: str
) -> None:
    """PM-NEV-09: the deployment floor is derived, not hard-coded."""
    approved, rejected = evaluate_recommendations(
        (buy("WFC"),),
        {"WFC": Money(amount=_WFC_COST)},
        cash_portfolio(
            str(_EQUITY),
            {"OTHER": 1},
            position_values={"OTHER": Money(amount=Decimal("12000.00"))},
        ),
        max_position_pct=Decimal("0.01"),
        max_positions=60,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
        sectors={"OTHER": "Other", "WFC": "Banking"},
        max_sector_pct=sector_cap,
        max_names_per_sector=names_cap,
    )

    sector = _approved_gate(approved, "max_sector_pct")
    assert rejected == ()
    assert sector.outcome == "not_evaluated"
    assert f"deployment_floor_pct={expected_floor}" in sector.detail


def test_zero_denominator_helper_does_not_emit_failed_zero_value() -> None:
    """PM-NEV-09: helper-level zero denominators do not report zero failed."""
    outcome = sector_exposure_outcome(
        sector="Banking",
        held_value=Decimal("0"),
        batch_value=Decimal("0"),
        cost=Decimal("1000.00"),
        equity_value=Decimal("0"),
        deployed_value=Decimal("0"),
        max_sector_pct=Decimal("0.30"),
        max_position_pct=Decimal("0.01"),
        max_names_per_sector=3,
    )

    assert outcome.value == 0.0
    assert outcome.outcome != GateStatus.FAILED
    assert outcome.outcome == GateStatus.NOT_EVALUATED


def _approved_gate(approved: tuple[OrderIntent, ...], name: str) -> GateOutcome:
    return next(item for item in approved[0].gate_report if item.name == name)
