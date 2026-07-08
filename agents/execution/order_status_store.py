"""Append-only broker order-status evidence for pending fills.

Agent: execution
Role: record broker order-status reads without mutating existing Fill facts.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.execution.broker import BrokerFill
    from kernel import GraphStore, Node

_CENTS = Decimal("100")
_ONE = Decimal("1")


def write_order_status(
    graph: GraphStore, *, fill_node: Node, broker_fill: BrokerFill
) -> Node:
    """Append one broker status read and link it to the Fill it refreshes."""
    created_at = datetime.now(tz=UTC).isoformat()
    node = graph.merge_node(
        "BrokerOrderStatus",
        f"broker-order-status:{fill_node.key}:{created_at}",
        {
            "fill_key": fill_node.key,
            "ticker": broker_fill.ticker,
            "quantity": broker_fill.quantity,
            "broker_order_id": broker_fill.broker_order_id,
            "status": broker_fill.status,
            "reason": broker_fill.reason,
            "price_cents": _money_to_cents(broker_fill),
            "created_at": created_at,
        },
    )
    graph.add_edge(node, fill_node, "REFRESHES")
    return node


def _money_to_cents(fill: BrokerFill) -> int:
    cents = (fill.price.amount * _CENTS).quantize(_ONE, rounding=ROUND_HALF_UP)
    return int(cents)
