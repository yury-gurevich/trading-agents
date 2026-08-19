"""Untracked-order acknowledgement helpers for the drop sweep.

Agent: execution
Role: remember no-Fill broker orders once without marking them dropped.
External I/O: injected GraphStore writes through callers.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from kernel import AgentFault

if TYPE_CHECKING:
    from agents.execution.broker import BrokerFill
    from kernel import FaultSink, GraphStore

ACK_LINEAGE_STATUS = "missing_fill_ack"
ACK_REASON = "missing Fill chain acknowledged once"
_ACK_LABEL = "BrokerOrderStatus"


def has_untracked_order_ack(graph: GraphStore, order: BrokerFill) -> bool:
    """Return whether this no-Fill broker order has already been reported."""
    return graph.get_node(_ACK_LABEL, untracked_order_ack_key(order)) is not None


def record_untracked_order_ack(
    graph: GraphStore, sink: FaultSink, order: BrokerFill, drop_status: str
) -> None:
    """Record first-sight no-Fill evidence, then emit the lineage fault."""
    if not has_untracked_order_ack(graph, order):
        observed_at = datetime.now(tz=UTC).isoformat()
        graph.merge_node(
            _ACK_LABEL,
            untracked_order_ack_key(order),
            {
                "broker_idempotency_key": order.idempotency_key,
                "ticker": order.ticker,
                "side": order.side,
                "quantity": order.quantity,
                "broker_order_id": order.broker_order_id,
                "status": drop_status,
                "reason": ACK_REASON,
                "lineage_status": ACK_LINEAGE_STATUS,
                "order_type": order.order_type or "",
                "created_at": observed_at,
            },
        )
    _record_untracked_drop(sink, order)


def untracked_order_ack_key(order: BrokerFill) -> str:
    """Return the stable acknowledgement key for one broker order."""
    return (
        f"broker-order-status:untracked:{order.idempotency_key}:{order.broker_order_id}"
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
