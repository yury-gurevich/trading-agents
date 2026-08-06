"""Alpaca account-state parsing for execution snapshots.

Agent: execution
Role: normalize broker account cash, equity and buying power into integer cents.
External I/O: none.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from agents.execution.broker import BrokerAccount

_CENTS = Decimal("100")
_ONE = Decimal("1")


def account_from_payload(payload: object) -> BrokerAccount:
    """Parse Alpaca account JSON into the execution broker account shape."""
    if not isinstance(payload, dict):
        raise ValueError("malformed_broker_account")
    return BrokerAccount(
        cash_cents=_money_field(payload, "cash"),
        equity_cents=_money_field(payload, "equity"),
        buying_power_cents=_money_field(payload, "buying_power"),
    )


def _money_field(payload: dict[object, object], name: str) -> int:
    value = payload.get(name)
    if value in (None, ""):
        raise ValueError(f"missing_broker_account_{name}")
    try:
        amount = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"invalid_broker_account_{name}") from exc
    return int((amount * _CENTS).quantize(_ONE, rounding=ROUND_HALF_UP))
