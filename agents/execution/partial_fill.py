"""The rest of a decision the broker ended after filling part of it.

Agent: execution
Role: tell the operator, once, that a partly filled order's remainder was not executed.
External I/O: the injected FaultSink.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.execution.broker import executed_quantity
from kernel import AgentFault

if TYPE_CHECKING:
    from agents.execution.broker import BrokerFill
    from kernel import FaultSink, Node


def report_unfilled_remainder(
    sink: FaultSink, fill_node: Node, broker_fill: BrokerFill
) -> None:
    """Warn once when a filled order executed fewer shares than it asked (DL-303)."""
    ordered = int(str(fill_node.props.get("quantity", 0)))
    filled = executed_quantity(broker_fill)
    if broker_fill.status != "filled" or filled >= ordered:
        return
    sink.submit(
        AgentFault(
            source_agent="execution",
            source_module="agents.execution.partial_fill",
            capability="refresh_pending_fills",
            severity="warning",
            error_type="UnfilledRemainder",
            message=(
                f"filled {filled} of {ordered} {broker_fill.ticker} "
                f"side={broker_fill.side}; the broker ended the rest "
                f"({broker_fill.order_status}) "
                f"broker_order_id={broker_fill.broker_order_id} "
                f"client_order_id={broker_fill.idempotency_key}"
            ),
            context={
                "fill_key": fill_node.key,
                "ticker": broker_fill.ticker,
                "ordered": ordered,
                "filled": filled,
                "broker_order_status": broker_fill.order_status,
            },
        )
    )
