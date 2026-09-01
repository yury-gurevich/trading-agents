"""Shared lifecycle predicates for execution broker facts.

Agent: contracts
Role: answer broker-order and graph-fact liveness questions across agents.
External I/O: injected GraphStore reads only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from kernel import GraphStore, Node

    class BrokerOrderLike(Protocol):
        """Structural broker order view needed for lifecycle decisions."""

        @property
        def idempotency_key(self) -> str:
            """Return the client idempotency key."""
            ...

        @property
        def broker_order_id(self) -> str:
            """Return the broker-assigned order id."""
            ...

        @property
        def order_type(self) -> str | None:
            """Return the broker order type when provided."""
            ...

        @property
        def status(self) -> str:
            """Return the broker status."""
            ...

        @property
        def reason(self) -> str | None:
            """Return the broker terminal reason when provided."""
            ...


BROKER_STOP_ORDER_TYPES = frozenset({"stop", "stop_limit"})
TERMINAL_FILL_BROKER_STATUSES = frozenset({"filled", "rejected"})
TERMINAL_BROKER_ORDER_STATUSES = frozenset(
    {"canceled", "cancelled", "expired", "filled", "rejected"}
)
RESOLVED_UNFILLED_BROKER_STATUSES = frozenset({"canceled", "cancelled", "expired"})
COMPLETED_EXIT_BROKER_STATUSES = frozenset({"filled", "partial", "partially_filled"})
FILLED_BROKER_STATUSES = frozenset({"filled"})


def is_live_broker_stop_fact(graph: GraphStore, stop: Node) -> bool:
    """Return whether a BrokerStopOrder still protects a position."""
    if _truthy_str(stop.props.get("cancelled_at")) is not None:
        return False
    fill = sibling_fill_for_broker_stop(graph, stop)
    if fill is None:
        return True
    return not is_terminal_fill_broker_status(fill.props.get("broker_status"))


def sibling_fill_for_broker_stop(graph: GraphStore, stop: Node) -> Node | None:
    """Find the Fill that carries the broker truth for one stop fact."""
    fill = graph.get_node("Fill", stop.key)
    if fill is not None:
        return fill
    broker_order_id = _truthy_str(stop.props.get("broker_order_id"))
    if broker_order_id is None:
        return None
    return next(
        (
            node
            for node in graph.list_nodes("Fill")
            if node.props.get("broker_order_id") == broker_order_id
        ),
        None,
    )


def is_resting_stop_fill(fill: Node) -> bool:
    """Return whether a Fill represents a resting broker-native stop."""
    return _truthy_str(fill.props.get("stop_order_key")) is not None


def is_open_order_fill(fill: Node) -> bool:
    """Return whether a Fill is a real non-stop order still awaiting outcome."""
    return (
        fill.label == "Fill"
        and fill.props.get("status") == "pending"
        and not is_terminal_fill_broker_status(fill.props.get("broker_status"))
        and fill.props.get("drop_reason") is None
        and not is_resting_stop_fill(fill)
    )


def is_terminal_fill_broker_status(value: object) -> bool:
    """Return whether a Fill broker_status stops future refresh."""
    return _normalise(value) in TERMINAL_FILL_BROKER_STATUSES


def is_broker_stop_order(order: BrokerOrderLike) -> bool:
    """Return whether broker metadata or the historic prefix marks a stop."""
    return order.idempotency_key.startswith("stop:") or (
        _normalise(order.order_type) in BROKER_STOP_ORDER_TYPES
    )


def is_live_broker_stop_order(order: BrokerOrderLike) -> bool:
    """Return whether a broker-side stop order is still live."""
    return is_broker_stop_order(order) and not is_terminal_broker_order_status(
        broker_order_lifecycle_status(order)
    )


def broker_order_lifecycle_status(order: BrokerOrderLike) -> str:
    """Return the broker-side lifecycle status, preserving terminal reasons."""
    reason = _normalise(order.reason)
    if reason in TERMINAL_BROKER_ORDER_STATUSES:
        return reason
    return _normalise(order.status)


def is_terminal_broker_order_status(value: object) -> bool:
    """Return whether broker order status means the order is no longer live."""
    return _normalise(value) in TERMINAL_BROKER_ORDER_STATUSES


def is_resolved_drop_status(value: object) -> bool:
    """Return whether a broker terminal reason is drop evidence."""
    return _normalise(value) in RESOLVED_UNFILLED_BROKER_STATUSES


def is_resolved_unfilled_broker_status(value: object) -> bool:
    """Return whether a broker status cannot carry realized PnL."""
    return _normalise(value) in RESOLVED_UNFILLED_BROKER_STATUSES


def is_completed_exit_fill(fill: Node) -> bool:
    """Return whether a prior exit Fill already completed the sell decision."""
    return _effective_fill_status(fill) in COMPLETED_EXIT_BROKER_STATUSES


def is_filled_buy_fill(fill: Node) -> bool:
    """Return whether a buy Fill has reached a filled broker outcome."""
    return (
        fill.props.get("side") == "buy"
        and _effective_fill_status(fill) in FILLED_BROKER_STATUSES
    )


def _effective_fill_status(fill: Node) -> str:
    return _normalise(fill.props.get("broker_status", fill.props.get("status")))


def _truthy_str(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _normalise(value: object) -> str:
    return str(value or "").lower()
