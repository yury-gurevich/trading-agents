"""Bounded order tolerance tests for ADR-0018.

Agent: execution
Role: prove approved orders become deterministic day limits around decision price.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from agents.execution import alpaca
from agents.execution.settings import ExecutionSettings
from contracts.common import Money
from kernel.config import AgentSettings, describe

_REF = Money(amount=Decimal("100.00"))


def test_order_body_builds_bounded_buy_limit_payload() -> None:
    """EXEC-NEV-01 / EXEC-NEV-02 / EXEC-NEV-03: buy is bounded above."""
    assert alpaca._order_body("run2:MSFT:buy", "MSFT", "buy", 7, _REF, 50) == {
        "symbol": "MSFT",
        "qty": "7",
        "side": "buy",
        "type": "limit",
        "limit_price": "100.50",
        "time_in_force": "day",
        "client_order_id": "run2:MSFT:buy",
    }


def test_order_body_builds_bounded_sell_limit_payload() -> None:
    """EXEC-NEV-01 / EXEC-NEV-02 / EXEC-TYP-01: sell is bounded below."""
    expected = {
        "symbol": "MSFT",
        "qty": "7",
        "side": "sell",
        "type": "limit",
        "limit_price": "99.50",
        "time_in_force": "day",
        "client_order_id": "run2:MSFT:sell",
    }
    assert alpaca._order_body("run2:MSFT:sell", "MSFT", "sell", 7, _REF, 50) == expected
    with pytest.raises(AssertionError):
        assert _inverted_sell_body() == expected


def test_order_body_rounds_half_cent_up_and_keeps_day_tif() -> None:
    """EXEC-IDM-01 / EXEC-TYP-01: Decimal cent rounding is deterministic."""
    body = alpaca._order_body(
        "run2:HALF:buy", "HALF", "buy", 1, Money(amount=Decimal("100.005")), 0
    )
    assert body["limit_price"] == "100.01"
    assert body["time_in_force"] == "day"


def test_execution_order_price_tolerance_is_declared_tunable() -> None:
    """EXEC-PARAM / ADR-0013: tolerance is bounded tunable metadata, not literal."""
    docs = {item.name: item for item in describe(ExecutionSettings)}
    tolerance = docs["order_price_tolerance_bps"]
    assert tolerance.default == 50
    assert tolerance.justification
    assert tolerance.minimum == 0.0
    assert tolerance.maximum == 500.0
    assert tolerance.unit == "bps"
    with pytest.raises(AssertionError):
        _assert_tunable(BareExecutionSettings)


def _inverted_sell_body() -> dict[str, object]:
    body = alpaca._order_body("run2:MSFT:buy", "MSFT", "buy", 7, _REF, 50)
    return {**body, "side": "sell", "client_order_id": "run2:MSFT:sell"}


def _assert_tunable(settings_cls: type[AgentSettings]) -> None:
    docs = {item.name: item for item in describe(settings_cls)}
    tolerance = docs["order_price_tolerance_bps"]
    assert tolerance.justification
    assert tolerance.minimum == 0.0
    assert tolerance.maximum == 500.0
    assert tolerance.unit == "bps"


class BareExecutionSettings(AgentSettings):
    order_price_tolerance_bps: int = 50
