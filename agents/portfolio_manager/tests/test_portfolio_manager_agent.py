"""PortfolioManagerAgent bus, sizing, risk, and graph tests.

Agent: portfolio_manager
Role: verify PM order decisions over the in-process bus.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal

from agents.portfolio_manager.settings import PortfolioManagerSettings
from agents.portfolio_manager.tests.helpers import (
    bar,
    cash_portfolio,
    evaluate_message,
    explain_message,
    recommendation,
    recommendation_set,
    seed_recommendation_nodes,
    wire_pm,
)
from contracts.common import Explanation
from contracts.portfolio_manager import OrderIntentSet


def test_evaluate_orders_sizes_order_and_stores_money_as_cents() -> None:
    """PM-IN-01 / PM-TRG-01 / PM-OUT-01 / PM-OUT-02 / PM-NEV-05 / PM-TYP-01 / PM-TYP-02:
    sizing produces whole-share OrderIntent; est_price is Decimal stored as cents."""
    payload = recommendation_set(recommendation("AAPL"))
    bus, graph, _ = wire_pm(
        source_bars=(bar("AAPL", 0, 100.0),),
        settings=PortfolioManagerSettings(
            starting_cash=Decimal("10000.00"),
            max_position_pct=Decimal("0.10"),
        ),
    )
    seed_recommendation_nodes(graph, payload)

    response = bus.request(evaluate_message(payload))

    result = OrderIntentSet.model_validate(response.payload)
    assert response.message_type == "response"
    assert [(item.ticker, item.quantity) for item in result.approved] == [("AAPL", 10)]
    assert result.approved[0].est_price.amount == Decimal("100.0")
    order = graph.get_node("OrderIntent", f"{result.run_id}:AAPL")
    assert order is not None
    assert order.props["est_price_cents"] == 10000
    recommendations = list(
        graph.descendants(order, max_depth=1, edge_types={"APPROVES"})
    )
    assert [node.label for node in recommendations] == ["Recommendation"]


def test_risk_rejects_when_position_limit_binds() -> None:
    """PM-NEV-04 / PM-STA-03 / PM-OUT-03: max_positions gate rejects excess."""
    payload = recommendation_set(recommendation("AAPL"))
    bus, _, _ = wire_pm(
        source_bars=(bar("AAPL", 0, 100.0),),
        settings=PortfolioManagerSettings(max_positions=1),
        portfolio=cash_portfolio("10000.00", {"MSFT": 1}),
    )

    response = bus.request(evaluate_message(payload))

    result = OrderIntentSet.model_validate(response.payload)
    assert result.approved == ()
    assert [(item.ticker, item.reason) for item in result.rejected] == [
        ("AAPL", "max_positions")
    ]


def test_risk_rejects_when_cash_buffer_binds() -> None:
    """PM-NEV-04 / PM-OUT-03: cash_buffer_pct gate rejects when insufficient."""
    payload = recommendation_set(recommendation("AAPL"))
    bus, _, _ = wire_pm(
        source_bars=(bar("AAPL", 0, 100.0),),
        settings=PortfolioManagerSettings(
            max_position_pct=Decimal("1.0"),
            cash_buffer_pct=Decimal("0.50"),
        ),
        portfolio=cash_portfolio("1000.00"),
    )

    response = bus.request(evaluate_message(payload))

    result = OrderIntentSet.model_validate(response.payload)
    assert result.approved == ()
    assert [(item.ticker, item.reason) for item in result.rejected] == [
        ("AAPL", "insufficient_cash")
    ]


def test_risk_rejects_when_order_is_below_minimum_quantity() -> None:
    """PM-NEV-05 / PM-NEV-04 / PM-OUT-03: min_quantity gate; never fractional."""
    payload = recommendation_set(recommendation("AAPL"))
    bus, _, _ = wire_pm(
        source_bars=(bar("AAPL", 0, 1000.0),),
        settings=PortfolioManagerSettings(
            max_position_pct=Decimal("0.01"),
            min_order_quantity=2,
        ),
        portfolio=cash_portfolio("10000.00"),
    )

    response = bus.request(evaluate_message(payload))

    result = OrderIntentSet.model_validate(response.payload)
    assert result.approved == ()
    assert [(item.ticker, item.reason) for item in result.rejected] == [
        ("AAPL", "below_min_quantity")
    ]


def test_degraded_provider_rejects_honestly_and_records_fault() -> None:
    """PM-NEV-02 / PM-OUT-04 / PM-FAIL-01 / PM-OBS-02: degraded provider → all rejected
    with "provider_degraded"; fault recorded; NEV-02 via bus only."""
    payload = recommendation_set(recommendation("AAPL"))
    bus, _, sink = wire_pm(fail_ohlcv=True)

    response = bus.request(evaluate_message(payload))

    result = OrderIntentSet.model_validate(response.payload)
    assert result.approved == ()
    assert [(item.ticker, item.reason) for item in result.rejected] == [
        ("AAPL", "provider_degraded")
    ]
    assert len(sink.faults) == 1
    assert sink.faults[0].source_module == "agents.portfolio_manager.agent"


def test_explain_decision_returns_grounded_explanation() -> None:
    """PM-IN-04 / PM-NEV-01: explain_decision returns Explanation; no broker call."""
    payload = recommendation_set(recommendation("AAPL"))
    bus, _, _ = wire_pm()

    response = bus.request(explain_message(payload))

    explanation = Explanation.model_validate(response.payload)
    assert response.message_type == "response"
    assert "Portfolio manager requests latest price" in explanation.summary
    assert explanation.evidence_refs == (
        "provider.get_market_data",
        "provider.get_regime",
    )
