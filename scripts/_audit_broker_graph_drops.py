"""Drop-specific broker/graph audit helpers.

Agent: tooling
Role: detect held positions that lost both a stop and a forced-exit attempt.
External I/O: injected graph and broker snapshots only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from contracts.broker_lifecycle import is_broker_stop_order

if TYPE_CHECKING:
    from agents.execution.broker import BrokerFill, BrokerPosition
    from kernel import GraphStore


@dataclass(frozen=True)
class DropAuditRow:
    """One audit row returned to the main audit renderer."""

    check: str
    verdict: str
    subject: str
    detail: str


def unprotected_dropped_exit_rows(
    graph: GraphStore,
    broker_positions: tuple[BrokerPosition, ...],
    broker_orders: tuple[BrokerFill, ...],
) -> tuple[DropAuditRow, ...]:
    """Return A5 rows for held names with a dropped sell and no full stop."""
    broker_qty = _broker_quantities(broker_positions)
    stop_qty = _pending_stop_quantities(broker_orders)
    dropped_sells = _dropped_sell_tickers(graph)
    rows: list[DropAuditRow] = []
    for ticker, held_qty in sorted(broker_qty.items()):
        if ticker not in dropped_sells or stop_qty.get(ticker, 0) >= held_qty:
            continue
        rows.append(
            DropAuditRow(
                "A5",
                "FAIL",
                ticker,
                "held position has no full live stop and a dropped sell decision",
            )
        )
    return tuple(rows)


def is_stop_order(order: BrokerFill) -> bool:
    """Return whether broker metadata or the historic prefix marks a stop."""
    return is_broker_stop_order(order)


def _dropped_sell_tickers(graph: GraphStore) -> frozenset[str]:
    return frozenset(
        str(node.props.get("ticker"))
        for node in graph.list_nodes("Fill")
        if node.props.get("side") == "sell" and node.props.get("drop_reason")
    )


def _pending_stop_quantities(orders: tuple[BrokerFill, ...]) -> dict[str, int]:
    quantities: dict[str, int] = {}
    for order in orders:
        if is_stop_order(order) and order.side == "sell" and order.status == "pending":
            quantities[order.ticker] = quantities.get(order.ticker, 0) + order.quantity
    return quantities


def _broker_quantities(positions: tuple[BrokerPosition, ...]) -> dict[str, int]:
    return {
        position.ticker: position.quantity
        for position in positions
        if position.quantity > 0
    }
