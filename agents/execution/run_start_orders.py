"""The broker orders a run start reads: narrowed where the broker can, never cut.

Agent: execution
Role: name the broker orders the graph still waits on, and read the run start's orders
      through the broker's narrow read when it offers one, else every order (DL-306).
External I/O: injected Broker reads.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple, Protocol, runtime_checkable

from agents.execution.fill_attempts import broker_idempotency_key
from contracts.broker_lifecycle import is_terminal_fill_broker_status

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from agents.execution.broker import Broker, BrokerFill
    from kernel import Node


class OrderRef(NamedTuple):
    """One broker order the graph waits on: its broker id (may be empty) and key."""

    broker_order_id: str
    idempotency_key: str


@runtime_checkable
class NarrowOrderReads(Protocol):
    """A broker that can read only the orders a run start needs."""

    def current_orders(
        self, waiting: Sequence[OrderRef] = ()
    ) -> tuple[BrokerFill, ...]:
        """Every open order, every recent order, and each waiting order."""
        ...  # pragma: no cover - protocol declaration only.


def run_start_orders(
    broker: Broker, waiting: Sequence[OrderRef] = ()
) -> tuple[BrokerFill, ...]:
    """The narrow read where the broker offers one; every order it knows otherwise."""
    if isinstance(broker, NarrowOrderReads):
        return broker.current_orders(waiting)
    return broker.fills()


def awaits_broker(fill: Node) -> bool:
    """Whether a Fill still waits on the broker's account (EXEC-STA-05)."""
    return fill.props.get("status") == "pending" and not is_terminal_fill_broker_status(
        fill.props.get("broker_status")
    )


def waiting_order_refs(fills: Iterable[Node]) -> tuple[OrderRef, ...]:
    """The broker order behind every Fill the refresh still waits on."""
    return tuple(
        OrderRef(
            str(fill.props.get("broker_order_id") or ""), broker_idempotency_key(fill)
        )
        for fill in fills
        if awaits_broker(fill)
    )
