"""Shared read model for broker-native stop orders.

Agent: contracts
Role: expose execution-owned BrokerStopOrder facts across agent boundaries.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contracts.common import Ticker
    from kernel import GraphStore, Node

BROKER_STOP_ORDER_LABEL = "BrokerStopOrder"


@dataclass(frozen=True)
class BrokerStopOrder:
    """Immutable placement fact for a resting broker stop."""

    key: str
    ticker: Ticker
    position_ref: str
    stop_price_cents: int
    broker_order_id: str
    placed_at: str
    cancelled_at: str | None = None


def broker_stop_order_key(position_ref: str, ticker: Ticker) -> str:
    """Return the shared graph key and broker client_order_id for a stop."""
    return f"stop:{position_ref}:{ticker}"


def active_broker_stop_refs(graph: GraphStore) -> frozenset[str]:
    """Return position_refs protected by non-cancelled BrokerStopOrder facts."""
    return frozenset(order.position_ref for order in active_broker_stop_orders(graph))


def active_broker_stop_orders(graph: GraphStore) -> tuple[BrokerStopOrder, ...]:
    """Return broker stops whose graph fact has not been cancelled."""
    return tuple(
        order for order in broker_stop_orders(graph) if order.cancelled_at is None
    )


def broker_stop_orders(graph: GraphStore) -> tuple[BrokerStopOrder, ...]:
    """Return all BrokerStopOrder graph facts in stable key order."""
    return tuple(
        _broker_stop_order(node)
        for node in sorted(
            graph.list_nodes(BROKER_STOP_ORDER_LABEL), key=lambda item: item.key
        )
    )


def _broker_stop_order(node: Node) -> BrokerStopOrder:
    props = node.props
    return BrokerStopOrder(
        key=node.key,
        ticker=str(props["ticker"]),
        position_ref=str(props["position_ref"]),
        stop_price_cents=int(props["stop_price_cents"]),
        broker_order_id=str(props["broker_order_id"]),
        placed_at=str(props["placed_at"]),
        cancelled_at=_optional_str(props.get("cancelled_at")),
    )


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) and value else None
