"""Low-level broker-stop submit and cancel actions.

Agent: execution
Role: keep stop-order side effects behind small helpers, and record provenance.
External I/O: injected Broker and GraphStore backends.

The graph facts these actions append live in broker_stop_writes.py (S225).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from agents.execution.broker import BrokerFill, BrokerRejectedError
from agents.execution.broker_stop_types import StopProvenance
from agents.execution.broker_stop_writes import (
    PROTECTED_BY_EDGE,
    STOP_FILL_EDGE,
    link_positions,
    write_stop_fill,
    write_stop_order,
)
from contracts.broker_stops import BROKER_STOP_ORDER_LABEL, BrokerStopOrder
from contracts.common import Money
from contracts.stop_rule import stop_price_cents
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from agents.execution.broker import Broker
    from contracts.positions import PositionStopThreshold
    from kernel import FaultSink, GraphStore

__all__ = [
    "PROTECTED_BY_EDGE",
    "STOP_FILL_EDGE",
    "cancel_stop",
    "place_stop",
]

# An unplanned call protects an already-adopted position: that is what every
# caller outside the two threshold builders is doing.
_DEFAULT_PROVENANCE = StopProvenance(
    stop_pct_source="position", derived_from="active_position"
)


def place_stop(
    graph: GraphStore,
    broker: Broker,
    sink: FaultSink,
    threshold: PositionStopThreshold,
    key: str,
    *,
    provenance: StopProvenance = _DEFAULT_PROVENANCE,
) -> BrokerFill:
    """Submit and record one broker-native stop for a position threshold."""
    stop_cents = stop_price_cents(threshold.opened_price_cents, threshold.stop_pct)
    fill = _submit_stop(broker, sink, threshold, key, stop_cents)
    fill_node = write_stop_fill(
        graph, threshold, key, fill, stop_cents, provenance=provenance
    )
    if fill.status == "rejected":
        return fill
    stop = write_stop_order(
        graph, threshold, key, fill, stop_cents, provenance=provenance
    )
    graph.add_edge(fill_node, stop, STOP_FILL_EDGE)
    link_positions(graph, threshold, stop)
    return fill


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


def _money_from_cents(cents: int) -> Money:
    return Money(amount=Decimal(cents) / Decimal("100"))
