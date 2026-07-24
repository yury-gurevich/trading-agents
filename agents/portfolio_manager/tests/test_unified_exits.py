"""Portfolio Manager unified-direction tests.

Agent: portfolio_manager
Role: prove PM sizes sells from held quantity and suppresses holds.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal

from agents.portfolio_manager.domain.concentration import SectorBook
from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.tests.helpers import (
    bar,
    cash_portfolio,
    evaluate_message,
    recommendation,
    recommendation_set,
    wire_pm,
)
from contracts.common import Money


def test_pm_sizes_sell_from_existing_position_quantity() -> None:
    """PM-OUT-01 / ADR-0016: sell recommendations become full-exit intents."""
    sell = recommendation("AAPL").model_copy(
        update={"action": "sell", "exit_trigger": "stop"}
    )

    approved, rejected = evaluate_recommendations(
        (sell,),
        {"AAPL": Money(amount=Decimal("25.00"))},
        cash_portfolio("10000.00", {"AAPL": 9}, position_refs={"AAPL": "exit-ref"}),
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
        ("AAPL", "sell", 9)
    ]
    assert approved[0].position_ref == "exit-ref"
    assert all(gate.passed for gate in approved[0].gate_report)
    assert [gate.name for gate in approved[0].gate_report] == [
        "sizing",
        "min_order_quantity",
        "max_positions",
        "cash_available",
    ]


def test_pm_rejects_hold_without_emitting_order() -> None:
    """PM-NEV-01 / ADR-0016: hold recommendations do not become buy orders."""
    hold = recommendation("AAPL").model_copy(update={"action": "hold"})

    approved, rejected = evaluate_recommendations(
        (hold,),
        {"AAPL": Money(amount=Decimal("25.00"))},
        cash_portfolio("10000.00", {"AAPL": 9}),
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
        ("AAPL", "hold_recommendation")
    ]


def test_pm_rejects_sell_below_minimum_quantity() -> None:
    sell = recommendation("AAPL").model_copy(update={"action": "sell"})

    approved, rejected = evaluate_recommendations(
        (sell,),
        {"AAPL": Money(amount=Decimal("25.00"))},
        cash_portfolio("10000.00", {"AAPL": 3}),
        max_position_pct=Decimal("0.10"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=5,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
    )

    assert approved == ()
    assert [(item.ticker, item.reason) for item in rejected] == [
        ("AAPL", "below_min_quantity")
    ]


def test_pm_rejects_unknown_recommendation_action() -> None:
    invalid = recommendation("AAPL").model_copy(update={"action": "trim"})

    approved, rejected = evaluate_recommendations(
        (invalid,),
        {"AAPL": Money(amount=Decimal("25.00"))},
        cash_portfolio("10000.00", {"AAPL": 9}),
        max_position_pct=Decimal("0.10"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
    )

    assert approved == ()
    assert rejected[0].reason == "unsupported_action"


def test_sector_book_records_exit_name_reduction() -> None:
    sell = recommendation("AAPL").model_copy(update={"action": "sell"})
    book = SectorBook(
        {"AAPL": "tech", "MSFT": "tech", "NVDA": "tech"}, ("AAPL", "MSFT")
    )

    before = book.exit_outcomes(sell, max_names_per_sector=3)
    book.record_exit("AAPL")
    after = book.outcomes(
        recommendation("NVDA"),
        Decimal("1.00"),
        Decimal("100.00"),
        max_sector_pct=Decimal("1.00"),
        max_names_per_sector=2,
    )

    assert before[-1].value == 1.0
    assert after[-1].value == 2.0


def test_sector_book_removes_last_exited_sector_name() -> None:
    sell = recommendation("AAPL").model_copy(update={"action": "sell"})
    book = SectorBook({"AAPL": "tech"}, ("AAPL",))

    book.record_exit("AAPL")
    outcomes = book.outcomes(
        recommendation("NVDA"),
        Decimal("1.00"),
        Decimal("100.00"),
        max_sector_pct=Decimal("1.00"),
        max_names_per_sector=1,
    )

    assert outcomes == ()
    assert book.exit_outcomes(sell, max_names_per_sector=0)[0].passed


def test_pm_bus_rebuilds_portfolio_from_graph_positions() -> None:
    sell = recommendation("AAPL").model_copy(update={"action": "sell"})
    bus, graph, sink = wire_pm(source_bars=(bar("AAPL", 0, 25.0),))
    graph.merge_node(
        "Position",
        "held:AAPL",
        {"ticker": "AAPL", "quantity": 6, "status": "open"},
    )

    response = bus.request(evaluate_message(recommendation_set(sell)))

    assert response.payload["approved"][0]["action"] == "sell"
    assert response.payload["approved"][0]["quantity"] == 6
    assert response.payload["approved"][0]["position_ref"]
    assert sink.faults == []
