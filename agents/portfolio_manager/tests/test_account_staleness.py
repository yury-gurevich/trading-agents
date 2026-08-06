"""Portfolio Manager stale-account tests.

Agent: portfolio_manager
Role: prove stale account facts block buys visibly without blocking sells.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal

from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.graph_portfolio import portfolio_from_graph
from agents.portfolio_manager.run import run_evaluation
from agents.portfolio_manager.settings import PortfolioManagerSettings
from agents.portfolio_manager.tests.account_helpers import (
    market,
    position,
    regime,
    snapshot,
)
from agents.portfolio_manager.tests.helpers import (
    bar,
    evaluate_message,
    recommendation,
    recommendation_set,
    wire_pm,
)
from contracts.common import Money
from contracts.portfolio_manager import OrderIntentSet
from kernel import CollectingFaultSink, InMemoryGraphStore


def test_sell_is_not_blocked_by_stale_account() -> None:
    """PM-NEV-01 / PM-NEV-04 / ADR-0016: stale account data never blocks a sell."""
    graph = InMemoryGraphStore()
    snapshot(graph, "sell-run", status="stale", account_status="stale")
    position(graph, "held:AAPL", "AAPL", 3, market_value_cents=30000)
    sell = recommendation("AAPL").model_copy(update={"action": "sell"})
    portfolio = portfolio_from_graph(graph, Decimal("100000.00"), run_id="sell-run")

    approved, rejected = evaluate_recommendations(
        (sell,),
        {"AAPL": Money(amount=Decimal("100.00"))},
        portfolio,
        max_position_pct=Decimal("0.10"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
    )

    assert rejected == ()
    assert [(item.ticker, item.action, item.quantity) for item in approved] == [
        ("AAPL", "sell", 3)
    ]


def test_missing_account_figures_block_buys_visibly() -> None:
    """PM-OBS-02 / PM-NEV-04: missing account facts reject buys and record a
    visible staleness Fault."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    snapshot(
        graph,
        "missing-account",
        status="fresh",
        account_status="fresh",
        include_account=False,
    )
    portfolio = portfolio_from_graph(
        graph, Decimal("100000.00"), run_id="missing-account"
    )

    assert portfolio.available_for_buys(Decimal("0.05"), Decimal("1")) == Decimal("0")

    result = run_evaluation(
        graph,
        recommendation_set=recommendation_set(recommendation("AAPL")),
        market=market("AAPL"),
        regime=regime(),
        settings=PortfolioManagerSettings(),
        portfolio=portfolio,
        sink=sink,
    )

    assert result.approved == ()
    assert [(item.ticker, item.reason) for item in result.rejected] == [
        ("AAPL", "account_unavailable")
    ]
    assert len(sink.faults) == 1
    assert "account state stale" in sink.faults[0].message


def test_pm_bus_rejects_buy_from_stale_snapshot_but_keeps_fault_visible() -> None:
    """PM-NEV-01 / PM-OBS-02: PM reads execution's graph fact, not the broker,
    and a stale account snapshot rejects buys visibly."""
    payload = recommendation_set(recommendation("AAPL"))
    bus, graph, sink = wire_pm(source_bars=(bar("AAPL", 0, 100.0),))
    snapshot(graph, "bus-stale", status="stale", account_status="stale")

    response = bus.request(evaluate_message(payload))

    result = OrderIntentSet.model_validate(response.payload)
    assert result.approved == ()
    assert result.rejected[0].reason == "account_unavailable"
    assert "account state stale" in sink.faults[0].message
