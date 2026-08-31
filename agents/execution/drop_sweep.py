"""Head-of-run stale order drop sweep.

Agent: execution
Role: cancel stale broker orders before the next decision run and record drops.
External I/O: injected Broker and GraphStore backends.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.execution.drop_sweep_ack import has_untracked_order_ack
from agents.execution.drop_sweep_records import (
    DROP_REASON,
    mark_execution_runs,
    record_drop,
    record_stop_mismatch,
    remember_execution_run,
)
from agents.execution.fill_attempts import latest_fill_attempt
from contracts.broker_lifecycle import (
    is_broker_stop_order,
    is_live_broker_stop_order,
    is_resolved_drop_status,
)
from contracts.broker_stops import active_broker_stop_orders
from kernel import fault_boundary

if TYPE_CHECKING:
    from agents.execution.broker import Broker, BrokerFill
    from kernel import FaultSink, GraphStore, Node


def sweep_unfilled_orders(
    graph: GraphStore, broker: Broker, sink: FaultSink, *, run_id: str
) -> int:
    """Cancel previous-run non-stop orders and record each dropped decision."""
    broker_orders = _read_broker_orders(broker, sink)
    dropped = 0
    touched_runs: set[str] = set()
    for order in broker_orders:
        recorded = False
        with fault_boundary(
            sink,
            agent="execution",
            module="agents.execution.drop_sweep",
            capability="drop_unfilled_orders",
            reraise=False,
        ):
            recorded = _sweep_order(graph, broker, sink, order, run_id, touched_runs)
        if recorded:
            dropped += 1
    with fault_boundary(
        sink,
        agent="execution",
        module="agents.execution.drop_sweep",
        capability="drop_unfilled_orders",
        reraise=False,
    ):
        mark_execution_runs(graph, touched_runs)
    return dropped


def _sweep_order(
    graph: GraphStore,
    broker: Broker,
    sink: FaultSink,
    order: BrokerFill,
    run_id: str,
    touched_runs: set[str],
) -> bool:
    fill = latest_fill_attempt(graph, order.idempotency_key)
    if _skip_order(graph, order, fill, run_id, sink):
        return False
    if _is_resolved_drop(order):
        recorded = record_drop(graph, sink, order, fill, _resolved_drop_status(order))
    elif order.status == "pending":
        _cancel_order(broker, order)
        recorded = record_drop(graph, sink, order, fill, "canceled")
    else:
        return False
    if recorded:
        remember_execution_run(graph, fill, touched_runs)
    return recorded


def _read_broker_orders(broker: Broker, sink: FaultSink) -> tuple[BrokerFill, ...]:
    with fault_boundary(
        sink,
        agent="execution",
        module="agents.execution.drop_sweep",
        capability="drop_unfilled_orders",
        reraise=False,
    ) as capture:
        orders = broker.fills()
    return () if capture.fault is not None else orders


def _skip_order(
    graph: GraphStore,
    order: BrokerFill,
    fill: Node | None,
    run_id: str,
    sink: FaultSink,
) -> bool:
    if not _pipeline_owned(order):
        return True
    if _already_dropped(fill):
        return True
    if _is_current_run(order, fill, run_id):
        return True
    if fill is None and has_untracked_order_ack(graph, order):
        return True
    return _is_stop_order(graph, order, sink)


def _pipeline_owned(order: BrokerFill) -> bool:
    key = order.idempotency_key
    return key.startswith("exit:") or key.count(":") >= 2


def _already_dropped(fill: Node | None) -> bool:
    return fill is not None and fill.props.get("drop_reason") == DROP_REASON


def _is_current_run(order: BrokerFill, fill: Node | None, run_id: str) -> bool:
    if order.idempotency_key.startswith(f"{run_id}:"):
        return True
    return fill is not None and fill.props.get("source_run_id") == run_id


def _is_stop_order(graph: GraphStore, order: BrokerFill, sink: FaultSink) -> bool:
    broker_stop = is_live_broker_stop_order(order)
    graph_stop = _tracked_as_stop(graph, order)
    if broker_stop != graph_stop:
        record_stop_mismatch(
            sink, order, broker_stop=broker_stop, graph_stop=graph_stop
        )
    return is_broker_stop_order(order) or graph_stop


def _tracked_as_stop(graph: GraphStore, order: BrokerFill) -> bool:
    return any(
        order.idempotency_key == stop.key
        or order.broker_order_id == stop.broker_order_id
        for stop in active_broker_stop_orders(graph)
    )


def _is_resolved_drop(order: BrokerFill) -> bool:
    return order.status == "rejected" and is_resolved_drop_status(
        _resolved_drop_status(order)
    )


def _resolved_drop_status(order: BrokerFill) -> str:
    return str(order.reason or "").lower()


def _cancel_order(broker: Broker, order: BrokerFill) -> None:
    try:
        broker.cancel(order.broker_order_id)
    except Exception as exc:
        message = (
            f"cancel failed for {order.ticker} "
            f"broker_order_id={order.broker_order_id}: {exc}"
        )
        raise RuntimeError(message) from exc
