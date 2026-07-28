"""Alpaca duplicate-order adoption tests.

Agent: execution
Role: prove duplicate client_order_id refusals adopt broker truth.
External I/O: none.
"""

from __future__ import annotations

import urllib.error
from decimal import Decimal
from email.message import Message
from types import MethodType

from agents.execution.alpaca import AlpacaBroker
from contracts.common import Money


def test_alpaca_duplicate_submit_adopts_existing_order_state() -> None:
    """DL-44 / DL-70 / S145 item 4: duplicate refusal adopts broker truth."""
    broker = AlpacaBroker(
        api_key="k",
        secret_key="s",  # noqa: S106 - test fixture, not a real secret
        base_url="https://alpaca.test",
        timeout=10,
    )
    calls: list[tuple[str, str, dict[str, object] | None]] = []

    def fake_request(
        _self: AlpacaBroker,
        method: str,
        path: str,
        body: dict[str, object] | None,
    ) -> object:
        calls.append((method, path, body))
        if method == "POST":
            raise urllib.error.HTTPError(
                "https://alpaca.test/v2/orders",
                422,
                "duplicate",
                Message(),
                None,
            )
        return {
            "id": "live-amd",
            "client_order_id": "exit:amd-ref:AMD:sell",
            "symbol": "AMD",
            "side": "sell",
            "qty": "55",
            "status": "accepted",
            "filled_avg_price": "",
        }

    broker._request = MethodType(fake_request, broker)  # type: ignore[method-assign]

    fill = broker.submit(
        "exit:amd-ref:AMD:sell", "AMD", "sell", 55, Money(amount=Decimal("189.28"))
    )

    assert fill.status == "pending"
    assert fill.broker_order_id == "live-amd"
    assert fill.price == Money(amount=Decimal("189.28"))
    assert calls[0][0] == "POST"
    assert calls[0][2] is not None
    assert calls[0][2]["client_order_id"] == "exit:amd-ref:AMD:sell"
    assert calls[1][0] == "GET"
    assert "client_order_id=exit%3Aamd-ref%3AAMD%3Asell" in calls[1][1]
