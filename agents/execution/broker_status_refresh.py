"""Broker status refresh property rules.

Agent: execution
Role: derive Fill broker-status updates from broker reconciliation reads.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.execution.broker import BrokerFill
    from kernel import Node

_BROKER_STATUS_PROP = "broker_status"
_BROKER_PRICE_CENTS_PROP = "broker_price_cents"
_BROKER_STATUS_REFRESHED_AT_PROP = "broker_status_refreshed_at"
_PARTIAL_STATUS = "partial"
_FILLED_STATUS = "filled"
_PRICE_STATUSES = frozenset({_FILLED_STATUS, _PARTIAL_STATUS})
_CENTS = Decimal("100")
_ONE = Decimal("1")


def broker_price_cents(fill: BrokerFill) -> int:
    """Return the broker fill price as integer cents."""
    cents = (fill.price.amount * _CENTS).quantize(_ONE, rounding=ROUND_HALF_UP)
    return int(cents)


def exit_price_cents(
    node: Node, broker_fill: BrokerFill, current_broker_price_cents: int
) -> int:
    """Return the price basis to use for this refresh's realized PnL."""
    if completes_partial_fill(node, broker_fill):
        return current_broker_price_cents
    return int(node.props.get(_BROKER_PRICE_CENTS_PROP, current_broker_price_cents))


def broker_status_props(
    node: Node, broker_fill: BrokerFill, current_broker_price_cents: int
) -> dict[str, object]:
    """Return Fill props for the broker status observation."""
    props: dict[str, object] = {}
    if _should_write_status(node, broker_fill):
        props = {
            _BROKER_STATUS_PROP: broker_fill.status,
            "broker_status_broker_order_id": broker_fill.broker_order_id,
            _BROKER_STATUS_REFRESHED_AT_PROP: datetime.now(tz=UTC).isoformat(),
        }
    if _should_write_price(node, broker_fill):
        props[_BROKER_PRICE_CENTS_PROP] = current_broker_price_cents
    return props


def completes_partial_fill(node: Node, broker_fill: BrokerFill) -> bool:
    """Return whether this broker read is the only allowed status advancement."""
    return (
        node.props.get(_BROKER_STATUS_PROP) == _PARTIAL_STATUS
        and broker_fill.status == _FILLED_STATUS
    )


def _should_write_status(node: Node, broker_fill: BrokerFill) -> bool:
    return _BROKER_STATUS_PROP not in node.props or completes_partial_fill(
        node, broker_fill
    )


def _should_write_price(node: Node, broker_fill: BrokerFill) -> bool:
    return broker_fill.status in _PRICE_STATUSES and (
        _BROKER_PRICE_CENTS_PROP not in node.props
        or completes_partial_fill(node, broker_fill)
    )
