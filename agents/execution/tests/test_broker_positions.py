"""Broker holdings-port tests.

Agent: execution
Role: verify read-only broker positions for PaperBroker and Alpaca.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from types import MethodType

import pytest

from agents.execution.alpaca import AlpacaBroker
from agents.execution.alpaca_positions import positions_from_payload
from agents.execution.broker import BrokerRejectedError, PaperBroker
from contracts.common import Money


def test_paper_broker_positions_track_the_in_memory_book() -> None:
    broker = PaperBroker(reject_tickers={"MSFT"})
    broker.submit("b1", "AAPL", "buy", 2, Money(amount=Decimal("10.00")))
    broker.submit("b2", "AAPL", "buy", 1, Money(amount=Decimal("13.00")))
    broker.submit("s1", "AAPL", "sell", 1, Money(amount=Decimal("11.00")))
    with pytest.raises(BrokerRejectedError):
        broker.submit("r1", "MSFT", "buy", 1, Money(amount=Decimal("10.00")))

    position = broker.positions()[0]

    assert position.ticker == "AAPL"
    assert position.quantity == 2
    assert position.avg_entry_cents == 1100
    assert position.market_value_cents == 2200

    broker.submit("s2", "AAPL", "sell", 2, Money(amount=Decimal("11.00")))
    assert broker.positions() == ()


def test_alpaca_position_payloads_normalize_decimal_strings() -> None:
    assert positions_from_payload({"not": "a list"}) == ()
    positions = positions_from_payload(
        [
            {"symbol": "", "qty": "1", "avg_entry_price": "1", "market_value": "1"},
            {
                "symbol": "AMD",
                "qty": "19",
                "avg_entry_price": "159.235",
                "market_value": "3045.50",
            },
        ]
    )

    assert len(positions) == 1
    assert positions[0].ticker == "AMD"
    assert positions[0].quantity == 19
    assert positions[0].avg_entry_cents == 15924
    assert positions[0].market_value_cents == 304550


def test_alpaca_broker_positions_reads_the_positions_endpoint() -> None:
    broker = AlpacaBroker(
        api_key="k",
        secret_key="s",  # noqa: S106 - test fixture, not a real secret
        base_url="https://alpaca.test",
        timeout=10,
    )
    seen: dict[str, object] = {}

    def fake_request(
        _self: AlpacaBroker, method: str, path: str, body: dict[str, object] | None
    ) -> object:
        seen["request"] = (method, path, body)
        return [
            {
                "symbol": "CSCO",
                "qty": "177",
                "avg_entry_price": "66.66",
                "market_value": "11798.82",
            }
        ]

    broker._request = MethodType(fake_request, broker)  # type: ignore[method-assign]

    positions = broker.positions()

    assert seen["request"] == ("GET", "/v2/positions", None)
    assert positions[0].ticker == "CSCO"
    assert positions[0].quantity == 177
