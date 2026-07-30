"""Portfolio Manager volatility passthrough tests.

Agent: portfolio_manager
Role: prove PM carries analyst ATR evidence without turning it into policy.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from agents.portfolio_manager.settings import PortfolioManagerSettings
from agents.portfolio_manager.tests.helpers import (
    bar,
    evaluate_message,
    recommendation,
    recommendation_set,
    seed_recommendation_nodes,
    wire_pm,
)
from contracts.analyst import QuantMetric
from contracts.portfolio_manager import OrderIntentSet


def test_pm_carries_atr_pct_onto_order_intent_unchanged() -> None:
    """PM-IDN-01 / PM-OUT-02 / PM-NEV-01 / PM-TYP-03: PM copies atr_pct."""
    rec = recommendation("AMD").model_copy(
        update={"quant_metrics": (QuantMetric(name="atr_pct", value=5.02),)}
    )
    payload = recommendation_set(rec)
    bus, graph, _sink = wire_pm(
        source_bars=(bar("AMD", 0, 100.0),),
        settings=PortfolioManagerSettings(
            starting_cash=Decimal("10000.00"),
            max_position_pct=Decimal("0.10"),
        ),
    )
    seed_recommendation_nodes(graph, payload)

    result = OrderIntentSet.model_validate(
        bus.request(evaluate_message(payload)).payload
    )

    assert result.approved[0].decision_atr_pct == 5.02
    order = graph.get_node("OrderIntent", f"{result.run_id}:AMD")
    assert order is not None
    assert order.props["decision_atr_pct"] == 5.02
    with pytest.raises(AssertionError):
        assert result.approved[0].decision_atr_pct == 5.0


def test_pm_missing_atr_pct_yields_none_not_a_guess() -> None:
    """PM-IDN-01 / PM-NEV-01 / PM-OBS-01: missing atr_pct stays absent."""
    payload = recommendation_set(recommendation("SCHW"))
    bus, graph, _sink = wire_pm(source_bars=(bar("SCHW", 0, 100.0),))
    seed_recommendation_nodes(graph, payload)

    result = OrderIntentSet.model_validate(
        bus.request(evaluate_message(payload)).payload
    )

    assert result.approved[0].decision_atr_pct is None
    order = graph.get_node("OrderIntent", f"{result.run_id}:SCHW")
    assert order is not None
    assert order.props["decision_atr_pct"] is None
    with pytest.raises(AssertionError):
        assert result.approved[0].decision_atr_pct == 1.0
