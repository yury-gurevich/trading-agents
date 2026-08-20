"""Broker-native stop placement and cleanup.

Agent: execution
Role: place one resting sell stop per active position and cancel stale stops.
External I/O: injected Broker and GraphStore backends.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from agents.execution.broker_stop_actions import cancel_stop, place_stop
from agents.execution.broker_stop_thresholds import (
    BrokerStopThresholdPlan,
    broker_stop_thresholds,
)
from agents.execution.filled_entry_stops import filled_entry_stop_thresholds
from agents.execution.settings import ExecutionSettings
from contracts.broker_stops import (
    active_broker_stop_orders,
    active_broker_stop_refs,
    next_broker_stop_order_key,
)
from contracts.positions import PositionStopThreshold, open_positions
from kernel import AgentFault

if TYPE_CHECKING:
    from agents.execution.broker import Broker, BrokerFill
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
    *,
    fallback_stop_pct: float | None = None,
) -> None:
    """Place missing sell stops for active positions not being sold this run."""
    broker_quantities = _fresh_snapshot_quantities(snapshot)
    if broker_quantities is None:
        return
    fallback = (
        ExecutionSettings().broker_stop_fallback_stop_pct
        if fallback_stop_pct is None
        else fallback_stop_pct
    )
    sold_tickers = {item.ticker for item in order_set.approved if item.action == "sell"}
    protected_refs = active_broker_stop_refs(graph)
    plan_set = broker_stop_thresholds(graph, fallback_stop_pct=fallback)
    plans = {plan.threshold.ticker: plan for plan in plan_set.plans}
    error_tickers: set[str] = set()
    for error in plan_set.errors:
        error_tickers.add(error.ticker)
        if error.ticker not in sold_tickers:
            _record_unprotected_fault(
                sink,
                error.ticker,
                broker_quantities.get(error.ticker, 0),
                f"no stop threshold: {error.reason}",
            )
    for entry_plan in filled_entry_stop_thresholds(
        graph,
        broker_quantities=broker_quantities,
        blocked_tickers=frozenset({*plans, *error_tickers}),
        fallback_stop_pct=fallback,
    ):
        plans[entry_plan.threshold.ticker] = entry_plan
    for ticker, quantity in sorted(broker_quantities.items()):
        if ticker in sold_tickers:
            continue
        if ticker in error_tickers:
            continue
        active_plan = plans.get(ticker)
        if active_plan is None:
            _record_unprotected_fault(
                sink, ticker, quantity, "no active graph position"
            )
            continue
        threshold = active_plan.threshold
        if not _broker_quantity_matches(threshold, broker_quantities):
            _record_unprotected_fault(
                sink,
                ticker,
                quantity,
                f"graph quantity {threshold.quantity} does not match broker quantity",
                position_ref=threshold.position_ref,
            )
            continue
        if threshold.position_ref in protected_refs:
            continue
        fill = _place_stop(graph, broker, sink, active_plan)
        if fill is None:
            _record_unprotected_fault(
                sink,
                ticker,
                quantity,
                "active BrokerStopOrder fact blocks duplicate stop placement",
                position_ref=threshold.position_ref,
            )
        elif fill.status == "rejected":
            _record_unprotected_fault(
                sink,
                ticker,
                quantity,
                f"stop submission rejected: {fill.reason or fill.status}",
                position_ref=threshold.position_ref,
            )


def _place_stop(
    graph: GraphStore,
    broker: Broker,
    sink: FaultSink,
    plan: BrokerStopThresholdPlan,
) -> BrokerFill | None:
    threshold = plan.threshold
    key = next_broker_stop_order_key(graph, threshold.position_ref, threshold.ticker)
    if key is None:
        return None
    return place_stop(
        graph,
        broker,
        sink,
        threshold,
        key,
        stop_pct_source=plan.stop_pct_source,
    )


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


def _record_unprotected_fault(
    sink: FaultSink,
    ticker: str,
    quantity: int,
    reason: str,
    *,
    position_ref: str | None = None,
) -> None:
    message = f"unprotected held position {ticker} qty={quantity}: {reason}"
    sink.submit(
        AgentFault(
            source_agent="execution",
            source_module="agents.execution.broker_stops",
            capability="place_broker_stops",
            severity="error",
            error_type="UnprotectedPosition",
            message=message,
            context={
                "ticker": ticker,
                "quantity": quantity,
                "reason": reason,
                "position_ref": position_ref,
            },
        )
    )
