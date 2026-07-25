"""Low-level broker-stop submit, write, and cancel actions.

Agent: execution
Role: keep stop-order side effects and graph facts behind small helpers.
External I/O: injected Broker and GraphStore backends.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from agents.execution.broker import BrokerFill, BrokerRejectedError
from contracts.broker_stops import BROKER_STOP_ORDER_LABEL, BrokerStopOrder
from contracts.common import Money
from contracts.positions import (
    PositionStopThreshold,
    active_position_nodes,
    position_basis_for_ref,
)
from contracts.stop_rule import stop_price_cents
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from agents.execution.broker import Broker
    from kernel import FaultSink, GraphStore, Node

PROTECTED_BY_EDGE = "PROTECTED_BY"
STOP_FILL_EDGE = "STOPS_WITH"


def place_stop(
    graph: GraphStore,
    broker: Broker,
    sink: FaultSink,
    threshold: PositionStopThreshold,
    key: str,
) -> None:
    """Submit and record one broker-native stop for a position threshold."""
    stop_cents = stop_price_cents(threshold.opened_price_cents, threshold.stop_pct)
    fill = _submit_stop(broker, sink, threshold, key, stop_cents)
    fill_node = _write_stop_fill(graph, threshold, key, fill, stop_cents)
    if fill.status == "rejected":
        return
    stop = _write_stop_order(graph, threshold, key, fill, stop_cents)
    graph.add_edge(fill_node, stop, STOP_FILL_EDGE)
    _link_positions(graph, threshold, stop)


def cancel_stop(
    graph: GraphStore, broker: Broker, sink: FaultSink, order: BrokerStopOrder
) -> None:
    """Cancel a stale broker stop and append its cancellation fact."""
    try:
        with fault_boundary(
            sink,
            agent="execution",
            module="agents.execution.broker_stop_actions",
            capability="cancel_stop",
            reraise=True,
        ):
            broker.cancel(order.broker_order_id)
    except Exception:
        return
    graph.merge_node(
        BROKER_STOP_ORDER_LABEL,
        order.key,
        {"cancelled_at": datetime.now(tz=UTC).isoformat()},
    )


def _submit_stop(
    broker: Broker,
    sink: FaultSink,
    threshold: PositionStopThreshold,
    key: str,
    stop_cents: int,
) -> BrokerFill:
    stop_price = _money_from_cents(stop_cents)
    try:
        with fault_boundary(
            sink,
            agent="execution",
            module="agents.execution.broker_stop_actions",
            capability="submit_stop",
            reraise=True,
        ):
            return broker.submit_stop(
                key, threshold.ticker, "sell", threshold.quantity, stop_price, "gtc"
            )
    except BrokerRejectedError as exc:
        return exc.fill
    except Exception as exc:
        return BrokerFill(
            idempotency_key=key,
            ticker=threshold.ticker,
            side="sell",
            quantity=threshold.quantity,
            price=stop_price,
            broker_order_id=f"rejected:{key}",
            status="rejected",
            reason=str(exc),
        )


def _write_stop_fill(
    graph: GraphStore,
    threshold: PositionStopThreshold,
    key: str,
    fill: BrokerFill,
    stop_cents: int,
) -> Node:
    return graph.merge_node(
        "Fill",
        key,
        {
            "ticker": threshold.ticker,
            "side": "sell",
            "quantity": threshold.quantity,
            "price_cents": stop_cents,
            "price_currency": fill.price.currency,
            "broker_order_id": fill.broker_order_id,
            "status": fill.status,
            "reason": fill.reason,
            "position_ref": threshold.position_ref,
            "stop_order_key": key,
        },
    )


def _write_stop_order(
    graph: GraphStore,
    threshold: PositionStopThreshold,
    key: str,
    fill: BrokerFill,
    stop_cents: int,
) -> Node:
    return graph.merge_node(
        BROKER_STOP_ORDER_LABEL,
        key,
        {
            "ticker": threshold.ticker,
            "position_ref": threshold.position_ref,
            "stop_price_cents": stop_cents,
            "broker_order_id": fill.broker_order_id,
            "placed_at": datetime.now(tz=UTC).isoformat(),
        },
    )


def _link_positions(
    graph: GraphStore, threshold: PositionStopThreshold, stop: Node
) -> None:
    basis = position_basis_for_ref(
        graph, position_ref=threshold.position_ref, ticker=threshold.ticker
    )
    if basis is None:
        return
    by_key = {node.key: node for node in active_position_nodes(graph)}
    for lot in basis.lots:
        position = by_key.get(lot.node_key)
        if position is not None:
            graph.add_edge(position, stop, PROTECTED_BY_EDGE)


def _money_from_cents(cents: int) -> Money:
    return Money(amount=Decimal(cents) / Decimal("100"))
