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
from contracts.portfolio_manager import OrderIntent


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
