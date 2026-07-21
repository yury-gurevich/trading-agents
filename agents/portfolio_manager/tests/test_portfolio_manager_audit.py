"""Portfolio Manager audit-truth regression tests.

Agent: portfolio_manager
Role: verify durable rejection evidence and explicit policy values.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal

from agents.portfolio_manager.domain.gate_report import position_outcomes
from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.store import write_order_decision
from agents.portfolio_manager.tests.helpers import (
    cash_portfolio,
    recommendation,
    recommendation_set,
)
from contracts.common import Money
from contracts.portfolio_manager import GateOutcome, RejectedOrder
from kernel import InMemoryGraphStore


def test_store_writes_queryable_rejection_evidence() -> None:
    """Kills agents.portfolio_manager.store.x_write_order_decision__mutmut_5."""
    graph = InMemoryGraphStore()
    payload = recommendation_set(recommendation("AAPL"))
    graph.merge_node("AnalystRun", payload.run_id, {"recommendation_count": 1})
    graph.merge_node("Recommendation", f"{payload.run_id}:AAPL", {"ticker": "AAPL"})

    provenance = write_order_decision(
        graph,
        recommendation_set=payload,
        approved=(),
        rejected=(RejectedOrder(ticker="AAPL", reason="max_positions"),),
    )

    rejection = graph.get_node("Rejection", f"{provenance.run_id}:AAPL")
    pm_run = graph.get_node("PMRun", provenance.run_id)
    assert rejection is not None
    assert pm_run is not None
    assert pm_run.props["approved_count"] == 0
    assert pm_run.props["rejected_count"] == 1
    assert pm_run.props["source_analyst_run_id"] == payload.run_id
    assert rejection.props["reason"] == "max_positions"
    assert [node.label for node in graph.descendants(rejection, max_depth=1)] == [
        "PMRun",
        "Recommendation",
    ]


def test_order_intent_preserves_deliberate_stop_and_target() -> None:
    # Explicit non-default policy (ratio 3.0) is preserved, not overridden by defaults.
    explicit_policy = recommendation("AAPL").model_copy(
        update={"suggested_stop_pct": 0.04, "suggested_target_pct": 0.12}
    )

    approved, rejected = evaluate_recommendations(
        (explicit_policy,),
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

    assert rejected == ()
    assert approved[0].stop_pct == 0.04
    assert approved[0].target_pct == 0.12


def test_order_intent_emits_pm_gate_report() -> None:
    approved, rejected = evaluate_recommendations(
        (recommendation("AAPL"),),
        {"AAPL": Money(amount=Decimal("100.00"))},
        cash_portfolio("10000.00", {"MSFT": 1}),
        max_position_pct=Decimal("0.10"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
        sectors={"AAPL": "Technology", "MSFT": "Technology"},
        max_sector_pct=Decimal("0.30"),
        max_names_per_sector=3,
    )

    names = {gate.name for gate in approved[0].gate_report}

    assert rejected == ()
    assert {
        "sizing",
        "min_order_quantity",
        "max_positions",
        "cash_available",
        "reward_risk",
        "max_sector_pct",
        "max_names_per_sector",
    } <= names
    assert all(gate.passed for gate in approved[0].gate_report)


def test_cash_gate_subtracts_reserved_cash_for_later_recommendations() -> None:
    """Kills
    agents.portfolio_manager.domain.gate_report.x_position_outcomes__mutmut_5.
    """
    approved, rejected = evaluate_recommendations(
        (
            recommendation("AAPL", confidence=0.90),
            recommendation("MSFT", confidence=0.80),
        ),
        {
            "AAPL": Money(amount=Decimal("300.00")),
            "MSFT": Money(amount=Decimal("300.00")),
        },
        cash_portfolio("1000.00"),
        max_position_pct=Decimal("0.60"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.10"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
    )

    assert [order.ticker for order in approved] == ["AAPL"]
    assert [(item.ticker, item.reason) for item in rejected] == [
        ("MSFT", "insufficient_cash")
    ]


def test_position_outcomes_hold_gate_boundaries() -> None:
    """Kills x_position_outcomes__mutmut_13."""
    observed = [
        (round(gate.value, 3), gate.threshold, gate.passed)
        for gate in (_position_gate("sizing", quantity) for quantity in (99, 100, 101))
    ]
    assert observed == [(0.099, 0.1, True), (0.1, 0.1, True), (0.101, 0.1, False)]

    observed = [
        (gate.value, gate.threshold, gate.passed)
        for gate in (
            _position_gate("min_order_quantity", quantity, min_quantity=5)
            for quantity in (4, 5, 6)
        )
    ]
    assert observed == [(4.0, 5.0, False), (5.0, 5.0, True), (6.0, 5.0, True)]


def test_position_outcomes_hold_capacity_boundaries() -> None:
    """Kills x_position_outcomes__mutmut_30."""
    observed = [
        (gate.value, gate.threshold, gate.passed)
        for gate in (
            _position_gate("max_positions", 1, held=held)
            for held in ({"MSFT"}, {"MSFT", "TSLA"}, {"MSFT", "TSLA", "NVDA"})
        )
    ]
    assert observed == [(2.0, 3.0, True), (3.0, 3.0, True), (4.0, 3.0, False)]

    observed = [
        (gate.value, gate.threshold, gate.passed)
        for gate in (
            _position_gate("cash_available", quantity, cash="100.00")
            for quantity in (89, 90, 91)
        )
    ]
    assert observed == [(89.0, 90.0, True), (90.0, 90.0, True), (91.0, 90.0, False)]


def _position_gate(
    name: str,
    quantity: int,
    *,
    cash: str = "1000.00",
    held: set[str] | None = None,
    min_quantity: int = 1,
) -> GateOutcome:
    outcomes = position_outcomes(
        item=recommendation("AAPL"),
        quantity=quantity,
        price=Money(amount=Decimal("1.00")),
        portfolio=cash_portfolio(cash),
        reserved_cash=Decimal("0"),
        open_tickers=held or {"MSFT"},
        max_position_pct=Decimal("0.10"),
        max_positions=3,
        cash_buffer_pct=Decimal("0.10"),
        min_order_quantity=min_quantity,
    )
    return next(outcome for outcome in outcomes if outcome.name == name)
