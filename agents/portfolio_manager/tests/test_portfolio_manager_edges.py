"""Portfolio Manager edge-case coverage tests.

Agent: portfolio_manager
Role: verify explainable edge cases without expanding sprint scope.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

import agents.portfolio_manager.agent as pm_agent_module
from agents.portfolio_manager import PortfolioManagerAgent
from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.domain.sizing import size_quantity
from agents.portfolio_manager.provider_client import latest_close_prices
from agents.portfolio_manager.store import write_order_decision
from agents.portfolio_manager.tests.helpers import (
    bar,
    cash_portfolio,
    evaluate_message,
    recommendation,
    recommendation_set,
    wire_pm,
)
from contracts.analyst import RecommendationSet
from contracts.common import Explanation, Money, Provenance
from contracts.portfolio_manager import OrderIntent, OrderIntentSet
from contracts.provider import DataQualityTrace, MarketData
from kernel import InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    import pytest


def test_empty_recommendations_return_explainable_empty_result() -> None:
    payload = recommendation_set()
    bus, _, _ = wire_pm()

    response = bus.request(evaluate_message(payload))

    result = OrderIntentSet.model_validate(response.payload)
    assert result.approved == ()
    assert result.rejected == ()
    assert (
        result.explanation.summary == "No orders approved; 0 recommendations rejected."
    )


def test_provider_unavailable_rejects_without_crashing() -> None:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    PortfolioManagerAgent(bus, graph=graph).bind()
    payload = recommendation_set(recommendation("AAPL"))

    response = bus.request(evaluate_message(payload))

    result = OrderIntentSet.model_validate(response.payload)
    assert result.approved == ()
    assert [(item.ticker, item.reason) for item in result.rejected] == [
        ("AAPL", "provider_unavailable")
    ]


def test_degraded_regime_rejects_honestly_and_records_fault() -> None:
    payload = recommendation_set(recommendation("AAPL"))
    bus, _, sink = wire_pm(source_bars=(bar("AAPL", 0, 100.0),), fail_regime=True)

    response = bus.request(evaluate_message(payload))

    result = OrderIntentSet.model_validate(response.payload)
    assert result.approved == ()
    assert [(item.ticker, item.reason) for item in result.rejected] == [
        ("AAPL", "provider_degraded")
    ]
    assert sink.faults[-1].message == "provider returned degraded regime data"


def test_evaluation_fault_rejects_all_recommendations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(pm_agent_module, "evaluate_recommendations", boom)
    payload = recommendation_set(recommendation("AAPL"))
    bus, _, sink = wire_pm(source_bars=(bar("AAPL", 0, 100.0),))

    response = bus.request(evaluate_message(payload))

    result = OrderIntentSet.model_validate(response.payload)
    assert result.approved == ()
    assert [(item.ticker, item.reason) for item in result.rejected] == [
        ("AAPL", "portfolio_evaluation_failed")
    ]
    assert sink.faults[-1].message == "boom"


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
    )

    assert approved == ()
    assert [(item.ticker, item.reason) for item in rejected] == [
        ("AAPL", "unsupported_action"),
        ("MSFT", "price_unavailable"),
    ]


def test_sizing_returns_zero_for_invalid_inputs() -> None:
    assert (
        size_quantity(
            portfolio_value=Decimal("0"),
            max_position_pct=Decimal("0.10"),
            est_price=Decimal("100"),
        )
        == 0
    )


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
