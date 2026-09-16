"""Correlation concentration denominator migration tests.

Agent: portfolio_manager
Role: prove correlated-cluster concentration divides by deployed capital.
External I/O: none.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest

from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.tests.helpers import cash_portfolio
from agents.portfolio_manager.tests.s184_helpers import buy
from contracts.common import Money
from contracts.provider import OHLCVBar

if TYPE_CHECKING:
    from contracts.portfolio_manager import GateOutcome, OrderIntent, RejectedOrder

_EQUITY = Decimal("102208.78")
_DEPLOYED = Decimal("21711.95")
_WFC_COST = Decimal("986.86")


def test_cluster_gate_uses_deployed_book_denominator() -> None:
    """PM-NEV-08 / PM-NEV-09: correlated_cluster_pct uses deployed capital."""
    approved, rejected = _evaluate_current_book(max_sector_pct=Decimal("1.00"))

    cluster = _approved_gate(approved, "correlated_cluster_pct")
    assert rejected == ()
    assert cluster.outcome == "passed"
    assert cluster.value == pytest.approx(0.0455, abs=0.0001)
    assert "denominator=deployed_capital" in cluster.detail


def test_current_book_is_above_the_derived_floors() -> None:
    """PM-NEV-06 / PM-NEV-08 / PM-NEV-09: today's deployed book is evaluated."""
    approved, rejected = _evaluate_current_book(max_sector_pct=Decimal("0.30"))

    sector = _approved_gate(approved, "max_sector_pct")
    cluster = _approved_gate(approved, "correlated_cluster_pct")
    assert rejected == ()
    assert sector.outcome == "passed"
    assert cluster.outcome == "passed"


def _evaluate_current_book(
    *, max_sector_pct: Decimal
) -> tuple[tuple[OrderIntent, ...], tuple[RejectedOrder, ...]]:
    return evaluate_recommendations(
        (buy("WFC"),),
        {"WFC": Money(amount=_WFC_COST)},
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
        sectors={"OTHER": "Other", "WFC": "Banking"},
        max_sector_pct=max_sector_pct,
        max_names_per_sector=3,
        correlation_bars=(*_bars("WFC", (0.01, -0.01)), *_bars("OTHER", (-0.01, 0.01))),
        correlation_lookback_days=120,
        correlation_threshold=0.70,
        max_correlated_cluster_pct=0.25,
        min_correlation_bars=60,
    )


def _approved_gate(approved: tuple[OrderIntent, ...], name: str) -> GateOutcome:
    return next(item for item in approved[0].gate_report if item.name == name)


def _bars(
    ticker: str, returns: tuple[float, float], *, days: int = 66
) -> tuple[OHLCVBar, ...]:
    close = 100.0
    rows: list[OHLCVBar] = []
    for offset in range(days):
        if offset:
            close *= 1.0 + returns[offset % len(returns)]
        day = date(2026, 1, 1) + timedelta(days=offset)
        rows.append(
            OHLCVBar(
                ticker=ticker,
                bar_date=day,
                open=close,
                high=close + 1.0,
                low=close - 1.0,
                close=close,
                volume=1_000_000,
            )
        )
    return tuple(rows)
