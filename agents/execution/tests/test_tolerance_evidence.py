"""Order tolerance evidence persistence tests.

Agent: execution
Role: prove applied and counterfactual tolerance facts are append-only Fill evidence.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from agents.execution.broker import BrokerFill
from agents.execution.order_tolerance import (
    OrderToleranceConfig,
    attach_order_tolerance,
    resolve_order_tolerance,
)
from agents.execution.settings import ExecutionSettings
from agents.execution.store import write_fills
from agents.execution.tests.helpers import (
    order,
    order_set,
    seed_order_nodes,
    submit_message,
    wire,
)
from agents.execution.tolerance_store_props import order_tolerance_props
from contracts.execution import ExecutionResult
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from collections.abc import Mapping

    from contracts.portfolio_manager import OrderIntent


def test_flat_mode_fill_records_scaled_counterfactual() -> None:
    """EXEC-OBS-01 / EXEC-IDM-01: flat orders record both tolerance modes."""
    bus, graph, _broker, _sink = wire(settings=ExecutionSettings())
    payload = order_set(order("AMD").model_copy(update={"decision_atr_pct": 3.0}))
    seed_order_nodes(graph, payload)

    result = ExecutionResult.model_validate(
        bus.request(submit_message(payload)).payload
    )

    fill = graph.get_node("Fill", f"{payload.run_id}:AMD:buy")
    assert result.submitted == 1
    assert fill is not None
    _assert_two_sided(fill.props)
    assert fill.props["order_tolerance_mode"] == "flat"
    assert fill.props["order_applied_tolerance_bps"] == 50
    assert fill.props["order_counterfactual_mode"] == "scaled"
    assert fill.props["order_counterfactual_tolerance_bps"] == 150
    assert fill.props["order_decision_atr_pct"] == 3.0
    assert fill.props["order_volatility_present"] is True


def test_scaled_mode_fill_records_flat_counterfactual() -> None:
    """EXEC-OBS-01 / EXEC-NEV-01: scaled orders keep the flat comparator."""
    bus, graph, _broker, _sink = wire(
        settings=ExecutionSettings(order_price_tolerance_mode="scaled")
    )
    payload = order_set(order("AMD").model_copy(update={"decision_atr_pct": 3.0}))
    seed_order_nodes(graph, payload)

    result = ExecutionResult.model_validate(
        bus.request(submit_message(payload)).payload
    )

    fill = graph.get_node("Fill", f"{payload.run_id}:AMD:buy")
    assert result.submitted == 1
    assert fill is not None
    _assert_two_sided(fill.props)
    assert fill.props["order_tolerance_mode"] == "scaled"
    assert fill.props["order_applied_tolerance_bps"] == 150
    assert fill.props["order_counterfactual_mode"] == "flat"
    assert fill.props["order_counterfactual_tolerance_bps"] == 50
    with pytest.raises(AssertionError):
        _assert_two_sided({"order_applied_tolerance_bps": 150})


def test_tolerance_evidence_replay_appends_without_rewriting() -> None:
    """EXEC-STA-03 / EXEC-OBS-01: changed tolerance evidence creates a new attempt."""
    graph = InMemoryGraphStore()
    key = "pm-run-fixture:AMD:buy"
    intent = order("AMD").model_copy(update={"decision_atr_pct": 3.0})
    flat = _fill_with_evidence(key, intent, ExecutionSettings())
    scaled = _fill_with_evidence(
        key, intent, ExecutionSettings(order_price_tolerance_mode="scaled")
    )
    payload = order_set(intent)

    write_fills(graph, run_id="execution-submit-flat", fills=(flat,), order_set=payload)
    write_fills(
        graph,
        run_id="execution-submit-scaled",
        fills=(scaled,),
        order_set=payload,
    )

    original = graph.get_node("Fill", key)
    replay = graph.get_node("Fill", f"{key}#1")
    assert original is not None
    assert replay is not None
    assert original.props["order_tolerance_mode"] == "flat"
    assert replay.props["order_tolerance_mode"] == "scaled"


def test_partial_tolerance_evidence_omits_absent_optional_prices() -> None:
    """EXEC-OBS-01: missing optional prices are not serialized as fake money."""
    fill = BrokerFill(
        idempotency_key="pm-run:AMD:buy",
        ticker="AMD",
        side="buy",
        quantity=1,
        price=order("AMD").est_price,
        broker_order_id="paper:pm-run:AMD:buy",
        status="pending",
        order_tolerance_mode="flat",
        order_applied_tolerance_bps=50,
    )

    props = order_tolerance_props(fill)

    assert props["order_tolerance_mode"] == "flat"
    assert "order_counterfactual_mode" not in props
    assert "order_decided_price_cents" not in props


def _fill_with_evidence(
    key: str, intent: OrderIntent, settings: ExecutionSettings
) -> BrokerFill:
    config = OrderToleranceConfig.from_settings(settings)
    evidence = resolve_order_tolerance(intent, "buy", config)
    fill = BrokerFill(
        idempotency_key=key,
        ticker=intent.ticker,
        side="buy",
        quantity=intent.quantity,
        price=intent.est_price,
        broker_order_id=f"paper:{key}",
        status="pending",
    )
    return attach_order_tolerance(fill, evidence)


def _assert_two_sided(props: Mapping[str, object]) -> None:
    for field in (
        "order_decided_price_cents",
        "order_applied_limit_price_cents",
        "order_counterfactual_limit_price_cents",
        "order_flat_limit_price_cents",
        "order_scaled_limit_price_cents",
    ):
        assert field in props
    assert props["order_decided_price_cents"] == 10000
    assert props["order_applied_limit_price_cents"]
    assert props["order_counterfactual_limit_price_cents"]
    assert props["order_flat_limit_price_cents"] == 10050
    assert props["order_scaled_limit_price_cents"] == 10150
