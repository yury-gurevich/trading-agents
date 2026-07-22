"""Alpaca paper-broker tests.

Agent: execution
Role: verify Alpaca order->fill mapping, status/price rules, malformed handling,
and the broker_from_settings selection — all without network.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from types import MethodType

import pytest

from agents.execution import alpaca
from agents.execution.alpaca import AlpacaBroker
from agents.execution.broker import BrokerFill, BrokerRejectedError, PaperBroker
from agents.execution.broker_factory import broker_from_settings
from agents.execution.settings import ExecutionSettings
from contracts.common import Money

_REF = Money(amount=Decimal("100.00"))


def _broker(submit_result: object) -> AlpacaBroker:
    broker = AlpacaBroker(
        api_key="k",
        secret_key="s",  # noqa: S106 - test fixture, not a real secret
        base_url="https://alpaca.test",
        timeout=10,
    )

    def fake_submit_or_get(_self: AlpacaBroker, _body: dict[str, object]) -> object:
        return submit_result

    broker._submit_or_get = MethodType(fake_submit_or_get, broker)  # type: ignore[method-assign]
    return broker


def _order(**overrides: object) -> dict[str, object]:
    order: dict[str, object] = {
        "id": "abc",
        "client_order_id": "run1:AAPL:buy",
        "symbol": "AAPL",
        "side": "buy",
        "qty": "10",
        "status": "filled",
        "filled_avg_price": "104.25",
    }
    order.update(overrides)
    return order


def test_order_body_builds_exact_market_order_payload() -> None:
    """Kills agents.execution.alpaca.x__order_body__mutmut_1."""
    assert alpaca._order_body("run2:MSFT:sell", "MSFT", "sell", 7) == {
        "symbol": "MSFT",
        "qty": "7",
        "side": "sell",
        "type": "market",
        "time_in_force": "day",
        "client_order_id": "run2:MSFT:sell",
    }


def test_fill_from_order_parses_all_fill_fields_exactly() -> None:
    """Kills agents.execution.alpaca.x__fill_from_order__mutmut_38."""
    order = _order(
        id="pf1",
        symbol="TSLA",
        side="sell",
        qty="3.0",
        status="partially_filled",
        filled_avg_price="199.125",
    )
    assert alpaca._fill_from_order(order, "run3:TSLA:sell", _REF) == BrokerFill(
        "run3:TSLA:sell",
        "TSLA",
        "sell",
        3,
        Money(amount=Decimal("199.125")),
        "pf1",
        "partial",
    )


def test_fill_from_order_rejects_malformed_and_sparse_orders_exactly() -> None:
    """Kills x__fill_from_order__mutmut_2 and x__fill_from_order__mutmut_14."""
    assert alpaca._fill_from_order("not-an-order", "run4:BAD:buy", _REF) == BrokerFill(
        "run4:BAD:buy", "", "buy", 0, _REF, "", "rejected", "malformed_broker_response"
    )
    assert alpaca._fill_from_order({}, "run5:EMPTY:buy", _REF) == BrokerFill(
        "run5:EMPTY:buy", "", "buy", 0, _REF, "", "rejected", "rejected"
    )


def test_fill_from_order_keeps_rejected_reason_exactly() -> None:
    """Kills agents.execution.alpaca.x__fill_from_order__mutmut_84."""
    order = _order(
        id="r2", side="sell", qty="4", status="canceled", filled_avg_price=""
    )
    assert alpaca._fill_from_order(order, "run6:AAPL:sell", _REF) == BrokerFill(
        "run6:AAPL:sell", "AAPL", "sell", 4, _REF, "r2", "rejected", "canceled"
    )


def test_price_of_uses_average_price_or_reference_exactly() -> None:
    """Kills agents.execution.alpaca.x__price_of__mutmut_6."""
    assert alpaca._price_of({"filled_avg_price": "104.2500"}, _REF).amount == Decimal(
        "104.2500"
    )
    assert alpaca._price_of({"filled_avg_price": ""}, _REF) is _REF
    assert alpaca._price_of({}, _REF) is _REF


def test_alpaca_maps_a_filled_order() -> None:
    fill = _broker(_order()).submit("run1:AAPL:buy", "AAPL", "buy", 10, _REF)
    assert fill.status == "filled"
    assert fill.price == Money(amount=Decimal("104.25"))
    assert fill.broker_order_id == "abc"
    assert fill.idempotency_key == "run1:AAPL:buy"
    assert (fill.ticker, fill.side, fill.quantity) == ("AAPL", "buy", 10)


def test_alpaca_pending_order_uses_reference_price() -> None:
    order = _order(
        id="p1",
        client_order_id="run1:MSFT:sell",
        symbol="MSFT",
        side="sell",
        qty="5",
        status="new",
        filled_avg_price="",
    )
    fill = _broker(order).submit("run1:MSFT:sell", "MSFT", "sell", 5, _REF)
    assert fill.status == "pending"
    assert fill.price == _REF
    assert fill.side == "sell"


def test_alpaca_rejected_order_raises_with_fill() -> None:
    order = {"id": "r1", "client_order_id": "k", "symbol": "AAPL", "status": "canceled"}
    with pytest.raises(BrokerRejectedError) as exc:
        _broker(order).submit("k", "AAPL", "buy", 10, _REF)
    assert exc.value.fill.status == "rejected"
    assert exc.value.fill.reason == "canceled"


def test_alpaca_malformed_response_is_rejected() -> None:
    with pytest.raises(BrokerRejectedError) as exc:
        _broker("not-an-order").submit("k", "AAPL", "buy", 10, _REF)
    assert exc.value.fill.reason == "malformed_broker_response"


def test_alpaca_fills_lists_orders_for_reconcile() -> None:
    broker = AlpacaBroker(
        api_key="k",
        secret_key="s",  # noqa: S106 - test fixture, not a real secret
        base_url="https://alpaca.test",
        timeout=10,
    )
    payload: list[object] = [
        _order(id="1", client_order_id="k1", filled_avg_price="104.00"),
        "garbage",
        {"id": "2", "symbol": "NODUP", "status": "new"},
        _order(
            id="3",
            client_order_id="k3",
            symbol="TSLA",
            qty="2",
            status="new",
            filled_avg_price="",
        ),
    ]

    def fake_list(_self: AlpacaBroker) -> list[object]:
        return payload

    broker._list_orders = MethodType(fake_list, broker)  # type: ignore[method-assign]
    fills = broker.fills()
    assert [f.idempotency_key for f in fills] == ["k1", "k3"]
    assert fills[0].price == Money(amount=Decimal("104.00"))
    assert fills[1].price == Money(amount=Decimal("0"))


def test_broker_from_settings_without_keys_is_paper() -> None:
    settings = ExecutionSettings(alpaca_api_key="", alpaca_secret_key="")
    assert isinstance(broker_from_settings(settings), PaperBroker)


def test_broker_from_settings_with_keys_is_alpaca() -> None:
    settings = ExecutionSettings(
        alpaca_api_key="k",
        alpaca_secret_key="s",  # noqa: S106 - test fixture, not a real secret
    )
    assert isinstance(broker_from_settings(settings), AlpacaBroker)
