"""Order submission helpers.

Agent: execution
Role: wrap broker submission under fault_boundary and maintain fill cache.
External I/O: Broker port calls.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.execution.broker import BrokerRejectedError
from agents.execution.domain.orders import BrokerOrder, rejected_broker_fill
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from agents.execution.broker import Broker, BrokerFill
    from kernel import FaultSink


def submit_order(
    broker: Broker,
    sink: FaultSink,
    order: BrokerOrder,
    capability: str,
) -> BrokerFill:
    """Submit one broker order and convert broker failures to rejected fills."""
    try:
        with fault_boundary(
            sink,
            agent="execution",
            module="agents.execution.domain.submit",
            capability=capability,
            reraise=True,
        ):
            return broker.submit(
                order.idempotency_key,
                order.ticker,
                order.side,
                order.quantity,
                order.limit_price,
            )
    except BrokerRejectedError as exc:
        return exc.fill
    except Exception as exc:
        return rejected_broker_fill(order, str(exc))


def remember(recorded: dict[str, BrokerFill], fills: tuple[BrokerFill, ...]) -> None:
    """Remember fills by idempotency key for later reconciliation."""
    for fill in fills:
        recorded[fill.idempotency_key] = fill
