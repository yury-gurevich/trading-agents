"""Alpaca stop-order adapter tests.

Agent: execution
Role: verify broker-native stop payloads and duplicate replay handling.
External I/O: none.
"""

from __future__ import annotations

import urllib.error
import urllib.parse
from decimal import Decimal
from email.message import Message
from io import BytesIO
from types import MethodType

import pytest

from agents.execution import alpaca
from agents.execution.alpaca import AlpacaBroker
from agents.execution.broker import BrokerRejectedError
from contracts.common import Money


def test_stop_order_body_builds_exact_gtc_stop_payload() -> None:
    """EXEC-NEV-03 / EXEC-IDM-02: stop submission remains a gtc stop order."""
    assert alpaca._stop_order_body(
        "stop:ref:MSFT", "MSFT", "sell", 7, Money(amount=Decimal("95.00")), "gtc"
    ) == {
        "symbol": "MSFT",
        "qty": "7",
        "side": "sell",
        "type": "stop",
        "stop_price": "95.00",
        "time_in_force": "gtc",
        "client_order_id": "stop:ref:MSFT",
    }


def test_alpaca_submit_stop_rests_pending_with_stop_body() -> None:
    seen: dict[str, object] = {}

    def fake_submit_or_get(_self: AlpacaBroker, body: dict[str, object]) -> object:
        seen["body"] = body
        return _order(
            id="stop-1",
            client_order_id=str(body["client_order_id"]),
            symbol=str(body["symbol"]),
            side=str(body["side"]),
            qty=str(body["qty"]),
            status="accepted",
            filled_avg_price="",
        )

    broker = _broker({})
    broker._submit_or_get = MethodType(fake_submit_or_get, broker)  # type: ignore[method-assign]

    fill = broker.submit_stop(
        "stop:ref:AAPL", "AAPL", "sell", 5, Money(amount=Decimal("95.00"))
    )

    assert seen["body"] == {
        "symbol": "AAPL",
        "qty": "5",
        "side": "sell",
        "type": "stop",
        "stop_price": "95.00",
        "time_in_force": "gtc",
        "client_order_id": "stop:ref:AAPL",
    }
    assert fill.status == "pending"
    assert fill.price == Money(amount=Decimal("95.00"))


def test_alpaca_submit_stop_raises_on_rejected_stop_order() -> None:
    broker = _broker(
        _order(
            id="stop-rejected",
            client_order_id="stop:ref:AAPL",
            symbol="AAPL",
            side="sell",
            qty="5",
            status="canceled",
            filled_avg_price="",
        )
    )

    with pytest.raises(BrokerRejectedError) as exc:
        broker.submit_stop(
            "stop:ref:AAPL", "AAPL", "sell", 5, Money(amount=Decimal("95.00"))
        )

    assert exc.value.fill.status == "rejected"
    assert exc.value.fill.reason == "canceled"


def test_submit_or_get_replays_422_by_client_order_id() -> None:
    broker = AlpacaBroker(
        api_key="k",
        secret_key="s",  # noqa: S106 - test fixture, not a real secret
        base_url="https://alpaca.test",
        timeout=10,
    )
    calls: list[tuple[str, str, dict[str, object] | None]] = []

    def fake_request(
        _self: AlpacaBroker, method: str, path: str, body: dict[str, object] | None
    ) -> object:
        calls.append((method, path, body))
        if method == "POST":
            raise urllib.error.HTTPError(path, 422, "duplicate", Message(), None)
        return _order(client_order_id="stop:ref:AAPL", status="accepted")

    broker._request = MethodType(fake_request, broker)  # type: ignore[method-assign]

    result = broker._submit_or_get({"client_order_id": "stop:ref:AAPL"})

    query = urllib.parse.parse_qs(urllib.parse.urlsplit(calls[1][1]).query)
    assert isinstance(result, dict)
    assert calls[0] == ("POST", "/v2/orders", {"client_order_id": "stop:ref:AAPL"})
    assert calls[1][0] == "GET"
    assert urllib.parse.urlsplit(calls[1][1]).path == "/v2/orders:by_client_order_id"
    assert query == {"client_order_id": ["stop:ref:AAPL"]}


def test_submit_or_get_keeps_non_duplicate_error_body() -> None:
    """EXEC-FAIL-01 / EXEC-OBS-02: broker refusal details remain observable."""
    broker = AlpacaBroker(
        api_key="k",
        secret_key="s",  # noqa: S106 - test fixture, not a real secret
        base_url="https://alpaca.test",
        timeout=10,
    )

    def fake_request(
        _self: AlpacaBroker,
        _method: str,
        path: str,
        _body: dict[str, object] | None,
    ) -> object:
        raise urllib.error.HTTPError(
            path,
            403,
            "Forbidden",
            Message(),
            BytesIO(b'{"message":"insufficient qty available"}'),
        )

    broker._request = MethodType(fake_request, broker)  # type: ignore[method-assign]

    with pytest.raises(RuntimeError, match="insufficient qty available"):
        broker._submit_or_get({"client_order_id": "stop:ref:AAPL"})


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
