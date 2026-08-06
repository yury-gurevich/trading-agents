"""Alpaca account read tests.

Agent: execution
Role: verify Alpaca account payload parsing without network access.
External I/O: none.
"""

from __future__ import annotations

from types import MethodType

import pytest

from agents.execution.alpaca import AlpacaBroker
from agents.execution.alpaca_account import account_from_payload


def test_alpaca_account_reads_and_parses_account_endpoint() -> None:
    """EXEC-IDN-03: the execution broker records cash, equity, and buying
    power facts from Alpaca's account endpoint."""
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
        return {
            "cash": "-104966.77",
            "equity": "104042.69",
            "buying_power": "165359.00",
        }

    broker._request = MethodType(fake_request, broker)  # type: ignore[method-assign]

    account = broker.account()

    assert seen["request"] == ("GET", "/v2/account", None)
    assert account.cash_cents == -10496677
    assert account.equity_cents == 10404269
    assert account.buying_power_cents == 16535900


def test_alpaca_account_rejects_malformed_account_payloads() -> None:
    """EXEC-OBS-02: malformed account payloads fail visibly before graph write."""
    with pytest.raises(ValueError, match="malformed_broker_account"):
        account_from_payload([])
    with pytest.raises(ValueError, match="missing_broker_account_cash"):
        account_from_payload({"equity": "1.00", "buying_power": "1.00"})
    with pytest.raises(ValueError, match="missing_broker_account_cash"):
        account_from_payload({"cash": "", "equity": "1.00", "buying_power": "1.00"})
    with pytest.raises(ValueError, match="invalid_broker_account_cash"):
        account_from_payload({"cash": "nope", "equity": "1.00", "buying_power": "1.00"})
