"""Broker-native stop placement and cleanup.

Agent: execution
Role: place one resting sell stop per active position and cancel stale stops.
External I/O: injected Broker and GraphStore backends.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from agents.execution.broker_stop_actions import cancel_stop, place_stop
from contracts.broker_stops import (
    BROKER_STOP_ORDER_LABEL,
    active_broker_stop_orders,
    active_broker_stop_refs,
    broker_stop_order_key,
)
from contracts.positions import (
    PositionStopThreshold,
    open_position_stop_thresholds,
    open_positions,
)

if TYPE_CHECKING:
    from agents.execution.broker import Broker
    from contracts.portfolio_manager import OrderIntentSet
    from kernel import FaultSink, GraphStore, Node


def reconcile_broker_stops(graph: GraphStore, broker: Broker, sink: FaultSink) -> None:
    """Cancel active stop facts whose position_ref is no longer active."""
    active_refs = frozenset(position.position_ref for position in open_positions(graph))
    for order in active_broker_stop_orders(graph):
        if order.position_ref not in active_refs:
            cancel_stop(graph, broker, sink, order)


def place_broker_stops(
    graph: GraphStore,
    broker: Broker,
    sink: FaultSink,
    order_set: OrderIntentSet,
    snapshot: Node | None,
) -> None:
    """Place missing sell stops for active positions not being sold this run."""
    broker_quantities = _fresh_snapshot_quantities(snapshot)
    if broker_quantities is None:
        return
    sold_tickers = {item.ticker for item in order_set.approved if item.action == "sell"}
    protected_refs = active_broker_stop_refs(graph)
    for threshold in open_position_stop_thresholds(graph):
        if not _broker_quantity_matches(threshold, broker_quantities):
            continue
        if threshold.ticker in sold_tickers or threshold.position_ref in protected_refs:
            continue
        _place_stop(graph, broker, sink, threshold)


def _place_stop(
    graph: GraphStore,
    broker: Broker,
    sink: FaultSink,
    threshold: PositionStopThreshold,
) -> None:
    key = broker_stop_order_key(threshold.position_ref, threshold.ticker)
    if graph.get_node(BROKER_STOP_ORDER_LABEL, key) is not None:
        return
    place_stop(graph, broker, sink, threshold, key)


def _fresh_snapshot_quantities(snapshot: Node | None) -> dict[str, int] | None:
    if snapshot is None or snapshot.props.get("status") != "fresh":
        return None
    quantities: dict[str, int] = {}
    for item in snapshot.props.get("holdings", ()):
        if not isinstance(item, Mapping):
            continue
        ticker = str(item.get("ticker", ""))
        quantity = int(item.get("quantity", 0))
        if ticker and quantity > 0:
            quantities[ticker] = quantity
    return quantities


def _broker_quantity_matches(
    threshold: PositionStopThreshold, broker_quantities: dict[str, int]
) -> bool:
    return broker_quantities.get(threshold.ticker) == threshold.quantity
