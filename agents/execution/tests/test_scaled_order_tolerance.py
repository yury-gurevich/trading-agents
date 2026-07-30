"""Volatility-scaled order tolerance tests for S149.

Agent: execution
Role: prove scaled tolerance is opt-in, bounded, and counterfactually measured.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Literal

import pytest
from pydantic import ValidationError

from agents.execution import alpaca
from agents.execution.order_tolerance import (
    OrderToleranceConfig,
    resolve_order_tolerance,
)
from agents.execution.settings import ExecutionSettings
from agents.execution.tests.helpers import (
    order,
    order_set,
    seed_order_nodes,
    submit_message,
    wire,
)
from contracts.common import Money
from contracts.execution import ExecutionResult
from kernel.config import AgentSettings, describe

if TYPE_CHECKING:
    from contracts.portfolio_manager import OrderIntent

_REF = Money(amount=Decimal("100.00"))


def test_flat_mode_ignores_volatility_and_matches_s148_payload() -> None:
    """EXEC-NEV-01 / EXEC-IDM-01: flat mode remains S148 byte-identical."""
    intent = order("MSFT").model_copy(update={"decision_atr_pct": 5.0})
    evidence = resolve_order_tolerance(intent, "buy", _config(mode="flat"))

    assert evidence.applied_tolerance_bps == 50
    assert alpaca._order_body("run2:MSFT:buy", "MSFT", "buy", 7, _REF, 50) == {
        "symbol": "MSFT",
        "qty": "7",
        "side": "buy",
        "type": "limit",
        "limit_price": "100.50",
        "time_in_force": "day",
        "client_order_id": "run2:MSFT:buy",
    }


def test_scaled_mode_resolves_exact_volatile_and_quiet_tolerances() -> None:
    """EXEC-IDM-01 / EXEC-NEV-01: scaled tolerance is deterministic per ATR."""
    volatile = order("AMD").model_copy(update={"decision_atr_pct": 3.0})
    quiet = order("SCHW").model_copy(update={"decision_atr_pct": 0.8})

    amd = resolve_order_tolerance(volatile, "buy", _config(mode="scaled"))
    schw = resolve_order_tolerance(quiet, "buy", _config(mode="scaled"))

    assert amd.applied_tolerance_bps == 150
    assert amd.applied_limit_price.amount == Decimal("101.50")
    assert schw.applied_tolerance_bps == 40
    assert schw.applied_limit_price.amount == Decimal("100.40")


def test_scaled_mode_floor_and_ceiling_clamps() -> None:
    """EXEC-FAIL-01 / EXEC-IDM-01: scaled rails bound tiny and huge ATR values."""
    tiny = order("CALM").model_copy(update={"decision_atr_pct": 0.1})
    huge = order("WILD").model_copy(update={"decision_atr_pct": 99.0})

    floor = resolve_order_tolerance(tiny, "buy", _config(mode="scaled"))
    ceiling = resolve_order_tolerance(huge, "buy", _config(mode="scaled"))

    assert floor.applied_tolerance_bps == 25
    assert ceiling.applied_tolerance_bps == 250
    with pytest.raises(AssertionError):
        assert ceiling.applied_tolerance_bps == 4950


def test_resolution_is_deterministic_for_same_intent_and_settings() -> None:
    """EXEC-IDM-01 / EXEC-IDM-02: same intent and settings yield same payload."""
    intent = order("AMD").model_copy(update={"decision_atr_pct": 3.0})
    config = _config(mode="scaled")

    first = resolve_order_tolerance(intent, "buy", config)
    second = resolve_order_tolerance(intent, "buy", config)

    assert first == second
    assert alpaca._order_body(
        "k", "AMD", "buy", 1, _REF, first.applied_tolerance_bps
    ) == (alpaca._order_body("k", "AMD", "buy", 1, _REF, second.applied_tolerance_bps))


def test_scaled_tolerance_knobs_are_declared_tunables_and_mode_is_bounded() -> None:
    """EXEC-PARAM / ADR-0013: scaled knobs are tunables and mode validates."""
    docs = {item.name: item for item in describe(ExecutionSettings)}
    for name in _SCALED_TUNABLES:
        assert docs[name].justification
        assert docs[name].minimum is not None
        assert docs[name].maximum is not None
        assert docs[name].unit
    with pytest.raises(AssertionError):
        _assert_scaled_tunables(BareScaledSettings)
    with pytest.raises(ValidationError):
        ExecutionSettings.model_validate({"order_price_tolerance_mode": "wide"})
    with pytest.raises(ValidationError, match="floor must be <= ceiling"):
        ExecutionSettings(
            scaled_order_price_tolerance_floor_bps=200,
            scaled_order_price_tolerance_ceiling_bps=100,
        )


def test_missing_volatility_scaled_mode_falls_back_and_still_submits() -> None:
    """EXEC-FAIL-01 / EXEC-NEV-01 / EXEC-OBS-01: missing ATR degrades to flat."""
    bus, graph, _broker, _sink = wire(
        settings=ExecutionSettings(order_price_tolerance_mode="scaled")
    )
    payload = order_set(order("AAPL"))
    seed_order_nodes(graph, payload)

    result = ExecutionResult.model_validate(
        bus.request(submit_message(payload)).payload
    )

    fill = graph.get_node("Fill", f"{payload.run_id}:AAPL:buy")
    assert result.submitted == 1
    assert result.rejected == 0
    assert fill is not None
    assert fill.props["order_applied_tolerance_bps"] == 50
    assert fill.props["order_volatility_fallback"] is True
    with pytest.raises(AssertionError):
        assert result.submitted == 0


def test_nonsensical_volatility_is_missing_or_clamped_not_trusted() -> None:
    """EXEC-FAIL-01 / EXEC-IDM-01: negative, NaN, and absurd ATR stay bounded."""
    negative = _constructed_intent("NEG", -1.0)
    nan = _constructed_intent("NAN", float("nan"))
    huge = _constructed_intent("HUGE", 99.0)
    config = _config(mode="scaled")

    assert resolve_order_tolerance(negative, "buy", config).applied_tolerance_bps == 50
    assert resolve_order_tolerance(nan, "buy", config).applied_tolerance_bps == 50
    assert resolve_order_tolerance(huge, "buy", config).applied_tolerance_bps == 250


_SCALED_TUNABLES = (
    "scaled_order_price_tolerance_atr_multiplier",
    "scaled_order_price_tolerance_floor_bps",
    "scaled_order_price_tolerance_ceiling_bps",
)


class BareScaledSettings(AgentSettings):
    scaled_order_price_tolerance_atr_multiplier: float = 0.50
    scaled_order_price_tolerance_floor_bps: int = 25
    scaled_order_price_tolerance_ceiling_bps: int = 250


def _config(mode: Literal["flat", "scaled"]) -> OrderToleranceConfig:
    return OrderToleranceConfig.from_settings(
        ExecutionSettings(order_price_tolerance_mode=mode)
    )


def _constructed_intent(ticker: str, atr_pct: float) -> OrderIntent:
    return order(ticker).model_copy(update={"decision_atr_pct": atr_pct})


def _assert_scaled_tunables(settings_cls: type[AgentSettings]) -> None:
    docs = {item.name: item for item in describe(settings_cls)}
    for name in _SCALED_TUNABLES:
        field = docs[name]
        assert field.justification
        assert field.minimum is not None
        assert field.maximum is not None
        assert field.unit
