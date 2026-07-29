"""Drop-sweep graph and fault record helpers.

Agent: execution
Role: append durable evidence for dropped broker decisions.
External I/O: injected GraphStore writes through callers.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from kernel import AgentFault

if TYPE_CHECKING:
    from agents.execution.broker import BrokerFill
    from kernel import FaultSink, GraphStore, Node

DROP_REASON = "unfilled at session end"
_EXECUTES_EDGE = "EXECUTES"
_EMITTED_BY_EDGE = "EMITTED_BY"
_EXECUTED_BY_EDGE = "EXECUTED_BY"
_REFRESHES_EDGE = "REFRESHES"


def record_drop(
    graph: GraphStore,
    sink: FaultSink,
    order: BrokerFill,
    fill: Node | None,
    broker_status: str,
) -> bool:
    """Append drop evidence for one broker order if its Fill chain exists."""
    if fill is None:
        _record_untracked_drop(sink, order)
        return False
    dropped_at = datetime.now(tz=UTC).isoformat()
    graph.merge_node(
        "Fill",
        fill.key,
        {
            "broker_status": broker_status,
            "broker_status_broker_order_id": order.broker_order_id,
            "broker_status_refreshed_at": dropped_at,
            "drop_reason": DROP_REASON,
            "dropped_at": dropped_at,
        },
    )
    status = graph.merge_node(
        "BrokerOrderStatus",
        f"broker-order-status:{fill.key}:drop:{dropped_at}",
        {
            "fill_key": fill.key,
            "ticker": order.ticker,
            "quantity": order.quantity,
            "broker_order_id": order.broker_order_id,
            "status": broker_status,
            "reason": DROP_REASON,
            "created_at": dropped_at,
        },
    )
    graph.add_edge(status, fill, _REFRESHES_EDGE)
    _record_dropped_fault(sink, order)
    return True


def record_stop_mismatch(
    sink: FaultSink, order: BrokerFill, *, broker_stop: bool, graph_stop: bool
) -> None:
    """Record a stop identity mismatch and leave the order exempt."""
    sink.submit(
        AgentFault(
            source_agent="execution",
            source_module="agents.execution.drop_sweep",
            capability="drop_unfilled_orders",
            severity="warning",
            error_type="BrokerStopIdentityMismatch",
            message=(
                f"stop identity mismatch for {order.idempotency_key}: "
                f"broker_stop={broker_stop} graph_stop={graph_stop}; order exempted"
            ),
        )
    )


def remember_execution_run(
    graph: GraphStore, fill: Node | None, touched_runs: set[str]
) -> None:
    """Add the execution run linked to a dropped Fill to the touched set."""
    run = _execution_run_for_fill(graph, fill)
    if run is not None:
        touched_runs.add(run.key)


def mark_execution_runs(graph: GraphStore, touched_runs: set[str]) -> None:
    """Append a dropped count to touched ExecutionRun nodes."""
    for execution_run_key in touched_runs:
        run = graph.get_node("ExecutionRun", execution_run_key)
        if run is None or "dropped" in run.props:
            continue
        graph.merge_node(
            "ExecutionRun", execution_run_key, {"dropped": _drop_count(graph, run)}
        )


def _record_dropped_fault(sink: FaultSink, order: BrokerFill) -> None:
    sink.submit(
        AgentFault(
            source_agent="execution",
            source_module="agents.execution.drop_sweep",
            capability="drop_unfilled_orders",
            severity="warning",
            error_type="DroppedDecision",
            message=(
                f"dropped unfilled order {order.ticker} side={order.side} "
                f"qty={order.quantity} decided_price={order.price.amount} "
                f"reason={DROP_REASON} broker_order_id={order.broker_order_id} "
                f"client_order_id={order.idempotency_key}"
            ),
        )
    )


def _record_untracked_drop(sink: FaultSink, order: BrokerFill) -> None:
    sink.submit(
        AgentFault(
            source_agent="execution",
            source_module="agents.execution.drop_sweep",
            capability="drop_unfilled_orders",
            severity="error",
            error_type="UntrackedOpenOrder",
            message=(
                f"open order {order.idempotency_key} for {order.ticker} "
                "has no Fill chain; durable drop lineage was not recorded"
            ),
        )
    )


def _drop_count(graph: GraphStore, execution_run: Node) -> int:
    return sum(
        _is_dropped(fill) for fill in _fills_for_execution_run(graph, execution_run)
    )


def _is_dropped(fill: Node) -> bool:
    return fill.props.get("drop_reason") == DROP_REASON


def _execution_run_for_fill(graph: GraphStore, fill: Node | None) -> Node | None:
    if fill is None:
        return None
    for order in graph.descendants(fill, max_depth=1, edge_types={_EXECUTES_EDGE}):
        for pm_run in graph.descendants(
            order, max_depth=1, edge_types={_EMITTED_BY_EDGE}
        ):
            return next(
                iter(
                    graph.descendants(
                        pm_run, max_depth=1, edge_types={_EXECUTED_BY_EDGE}
                    )
                ),
                None,
            )
    return None


def _fills_for_execution_run(
    graph: GraphStore, execution_run: Node
) -> tuple[Node, ...]:
    fills: list[Node] = []
    for pm_run in graph.ancestors(
        execution_run, max_depth=1, edge_types={_EXECUTED_BY_EDGE}
    ):
        for order in graph.ancestors(
            pm_run, max_depth=1, edge_types={_EMITTED_BY_EDGE}
        ):
            fills.extend(
                graph.ancestors(order, max_depth=1, edge_types={_EXECUTES_EDGE})
            )
    return tuple(fills)
