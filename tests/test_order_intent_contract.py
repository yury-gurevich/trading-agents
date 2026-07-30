"""Portfolio manager OrderIntent contract compatibility tests.

Agent: contracts (portfolio_manager)
Role: verify additive execution metadata remains backward compatible.
External I/O: none.
"""

from __future__ import annotations

from contracts.portfolio_manager import OrderIntent


def test_order_intent_decision_atr_pct_is_optional_and_round_trips() -> None:
    """PM-TYP-03 / EXEC-IN-01: legacy intents validate with no ATR field."""
    legacy = OrderIntent.model_validate(
        {
            "ticker": "AAPL",
            "action": "buy",
            "quantity": 1,
            "est_price": {"amount": "100.00", "currency": "USD"},
            "rationale": {"summary": "fixture"},
        }
    )
    current = legacy.model_copy(update={"decision_atr_pct": 2.51})

    parsed = OrderIntent.model_validate(current.model_dump(mode="json"))

    assert legacy.decision_atr_pct is None
    assert parsed.decision_atr_pct == 2.51
