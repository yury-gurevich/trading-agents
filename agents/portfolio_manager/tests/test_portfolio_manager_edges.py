"""Portfolio Manager domain and store edge-case tests.

Agent: portfolio_manager
Role: verify sizing, provider price selection, and optional graph lineage edges.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal

from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.domain.sizing import size_quantity
from agents.portfolio_manager.provider_client import latest_close_prices
from agents.portfolio_manager.store import write_order_decision
from agents.portfolio_manager.tests.helpers import (
    bar,
    cash_portfolio,
    recommendation,
    recommendation_set,
)
from contracts.analyst import RecommendationSet
from contracts.common import Explanation, Money, Provenance
from contracts.portfolio_manager import OrderIntent
from contracts.provider import DataQualityTrace, MarketData
from kernel import InMemoryGraphStore


def test_risk_prechecks_reject_unsupported_action_and_missing_price() -> None:
    sell = recommendation("AAPL").model_copy(update={"action": "sell"})
    missing_price = recommendation("MSFT")

    approved, rejected = evaluate_recommendations(
        (sell, missing_price),
        {"AAPL": Money(amount=Decimal("100.00"))},
        cash_portfolio("10000.00"),
        max_position_pct=Decimal("0.10"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
    )

    assert approved == ()
    assert [(item.ticker, item.reason) for item in rejected] == [
        ("AAPL", "unsupported_action"),
        ("MSFT", "price_unavailable"),
    ]


def test_sizing_returns_zero_for_invalid_inputs() -> None:
    """Kills agents.portfolio_manager.domain.sizing.x_size_quantity__mutmut_1.

    Also kills agents.portfolio_manager.domain.sizing.x_size_quantity__mutmut_2.
    """
    valid = {
        "portfolio_value": Decimal("1000.00"),
        "max_position_pct": Decimal("0.10"),
        "est_price": Decimal("100.00"),
    }

    assert size_quantity(**valid) == 1
    for field in valid:
        values = dict(valid)
        values[field] = Decimal("0")
        assert size_quantity(**values) == 0

        values[field] = Decimal("-0.01")
        assert size_quantity(**values) == 0

    assert (
        size_quantity(
            portfolio_value=Decimal("-1000.00"),
            max_position_pct=Decimal("1.00"),
            est_price=Decimal("1.00"),
        )
        == 0
    )


def test_sizing_holds_whole_share_budget_boundary() -> None:
    """Kills agents.portfolio_manager.domain.sizing.x_size_quantity__mutmut_7.

    Also kills agents.portfolio_manager.domain.sizing.x_size_quantity__mutmut_4 and
    agents.portfolio_manager.domain.sizing.x_size_quantity__mutmut_8.
    """
    budget = {
        "portfolio_value": Decimal("1000.00"),
        "max_position_pct": Decimal("0.10"),
    }

    assert size_quantity(**budget, est_price=Decimal("100.01")) == 0
    assert size_quantity(**budget, est_price=Decimal("100.00")) == 1
    assert size_quantity(**budget, est_price=Decimal("99.99")) == 1
    assert (
        size_quantity(
            portfolio_value=Decimal("1.00"),
            max_position_pct=Decimal("1.00"),
            est_price=Decimal("1.00"),
        )
        == 1
    )


def test_zero_value_portfolio_rejects_below_minimum_quantity() -> None:
    approved, rejected = evaluate_recommendations(
        (recommendation("AAPL"),),
        {"AAPL": Money(amount=Decimal("100.00"))},
        cash_portfolio("0.00"),
        max_position_pct=Decimal("0.10"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
    )

    assert approved == ()
    assert [(item.ticker, item.reason) for item in rejected] == [
        ("AAPL", "below_min_quantity")
    ]


def test_latest_close_prices_keeps_newest_bar() -> None:
    prices = latest_close_prices(
        MarketData(
            bars=(bar("AAPL", 0, 101.0), bar("AAPL", 2, 99.0)),
            quality=DataQualityTrace(requested=1, returned=2),
            provenance=Provenance(run_id="provider", source_agent="provider"),
        )
    )

    assert prices["AAPL"].amount == Decimal("101.0")


def test_store_skips_missing_recommendation_node() -> None:
    graph = InMemoryGraphStore()
    payload = recommendation_set(recommendation("AAPL"))

    provenance = write_order_decision(
        graph,
        recommendation_set=payload,
        approved=(_order("AAPL"),),
        rejected=(),
    )

    order = graph.get_node("OrderIntent", f"{provenance.run_id}:AAPL")
    assert order is not None
    assert list(graph.descendants(order, max_depth=1, edge_types={"APPROVES"})) == []


def test_store_skips_absent_analyst_graph_id() -> None:
    graph = InMemoryGraphStore()
    payload = RecommendationSet(
        run_id="analyst-run-no-graph",
        recommendations=(recommendation("AAPL"),),
        rejections=(),
        explanation=Explanation(summary="fixture"),
        provenance=Provenance(run_id="analyst-run-no-graph", source_agent="analyst"),
    )

    provenance = write_order_decision(
        graph,
        recommendation_set=payload,
        approved=(_order("AAPL"),),
        rejected=(),
    )

    order = graph.get_node("OrderIntent", f"{provenance.run_id}:AAPL")
    assert order is not None
    assert list(graph.descendants(order, max_depth=1, edge_types={"APPROVES"})) == []


def _order(ticker: str) -> OrderIntent:
    return OrderIntent(
        ticker=ticker,
        action="buy",
        quantity=1,
        est_price=Money(amount=Decimal("100.00")),
        rationale=Explanation(summary="fixture order"),
    )
