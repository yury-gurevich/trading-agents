"""Alpaca position payload parsing for the execution broker adapter.

Agent: execution
Role: normalize Alpaca holding snapshots into broker-port value objects.
External I/O: none.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from agents.execution.broker import BrokerPosition

_CENTS = Decimal("100")
_ONE = Decimal("1")


def positions_from_payload(payload: object) -> tuple[BrokerPosition, ...]:
    """Return broker positions from Alpaca's /v2/positions response."""
    if not isinstance(payload, list):
        return ()
    positions = [
        _position_from_item(item) for item in payload if isinstance(item, dict)
    ]
    return tuple(item for item in positions if item is not None)


def _position_from_item(item: dict[str, object]) -> BrokerPosition | None:
    ticker = str(item.get("symbol", "")).strip()
    if not ticker:
        return None
    return BrokerPosition(
        ticker=ticker,
        quantity=_quantity(item.get("qty", "0")),
        avg_entry_cents=_cents(item.get("avg_entry_price", "0")),
        market_value_cents=_cents(item.get("market_value", "0")),
    )


def _quantity(raw: object) -> int:
    return int(Decimal(str(raw)))


def _cents(raw: object) -> int:
    cents = (Decimal(str(raw)) * _CENTS).quantize(_ONE, rounding=ROUND_HALF_UP)
    return int(cents)
