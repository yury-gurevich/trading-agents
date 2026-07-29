"""Broker/graph audit implementation.

Agent: tooling
Role: compare broker holdings, stop protection, and Fill lineage.
External I/O: injected graph and broker snapshots only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from scripts._audit_broker_graph_drops import (
    is_stop_order,
    unprotected_dropped_exit_rows,
)

from agents.execution.fill_attempts import fill_attempt_chain
from contracts.positions import is_active_position_node

if TYPE_CHECKING:
    from agents.execution.broker import BrokerFill, BrokerPosition
    from kernel import GraphStore, Node

_ALLOWLIST = {
    "dep-broker-probe-": "dependency probe order; no pipeline Fill expected",
    "probe-s138-": "S138 broker-stop live probe order; no pipeline Fill expected",
}


@dataclass(frozen=True)
class AuditRow:
    """One rendered audit row."""

    check: str
    verdict: str
    subject: str
    detail: str


@dataclass(frozen=True)
class AuditReport:
    """Full audit result."""

    rows: tuple[AuditRow, ...]
    failures: int


def audit_graph(
    graph: GraphStore,
    broker_positions: tuple[BrokerPosition, ...],
    broker_orders: tuple[BrokerFill, ...],
) -> AuditReport:
    """Run all read-only broker/graph checks."""
    rows: list[AuditRow] = []
    _audit_positions(graph, broker_positions, rows)
    _audit_stops(broker_positions, broker_orders, rows)
    rows.extend(
        AuditRow(row.check, row.verdict, row.subject, row.detail)
        for row in unprotected_dropped_exit_rows(graph, broker_positions, broker_orders)
    )
    _audit_orphan_fills(graph, broker_orders, rows)
    _audit_flags(graph, rows)
    failures = sum(row.verdict == "FAIL" for row in rows)
    return AuditReport(rows=tuple(rows), failures=failures)


def print_report(report: AuditReport) -> None:
    """Print the tab-separated audit report."""
    print("check\tverdict\tsubject\tdetail")
    for row in report.rows:
        print(f"{row.check}\t{row.verdict}\t{row.subject}\t{row.detail}")
    print(f"totals failures={report.failures}")


def _audit_positions(
    graph: GraphStore,
    broker_positions: tuple[BrokerPosition, ...],
    rows: list[AuditRow],
) -> None:
    broker_qty = _broker_quantities(broker_positions)
    active = _active_positions_by_ticker(graph)
    for ticker in sorted(set(broker_qty) | set(active)):
        nodes = active.get(ticker, ())
        graph_qty = sum(int(node.props.get("quantity", 0)) for node in nodes)
        ok = len(nodes) == 1 and graph_qty == broker_qty.get(ticker, 0)
        rows.append(
            AuditRow(
                "A1",
                "OK" if ok else "FAIL",
                ticker,
                (
                    f"active_nodes={len(nodes)} graph_qty={graph_qty} "
                    f"broker_qty={broker_qty.get(ticker, 0)}"
                ),
            )
        )


def _audit_stops(
    broker_positions: tuple[BrokerPosition, ...],
    broker_orders: tuple[BrokerFill, ...],
    rows: list[AuditRow],
) -> None:
    broker_qty = _broker_quantities(broker_positions)
    stop_qty = _pending_stop_quantities(broker_orders)
    closing_qty = _pending_closing_sell_quantities(broker_orders)
    for ticker, held_qty in sorted(broker_qty.items()):
        if closing_qty.get(ticker, 0) >= held_qty:
            rows.append(AuditRow("A2", "SKIP", ticker, "pending full-exit sell"))
            continue
        qty = stop_qty.get(ticker, 0)
        rows.append(
            AuditRow(
                "A2",
                "OK" if qty == held_qty else "FAIL",
                ticker,
                f"held={held_qty} stop_qty={qty}",
            )
        )


def _audit_orphan_fills(
    graph: GraphStore, broker_orders: tuple[BrokerFill, ...], rows: list[AuditRow]
) -> None:
    for order in sorted(broker_orders, key=lambda item: item.idempotency_key):
        reason = _allowlist_reason(order.idempotency_key)
        if reason is not None:
            rows.append(AuditRow("A3", "SKIP", order.idempotency_key, reason))
            continue
        if not fill_attempt_chain(graph, order.idempotency_key):
            detail = (
                f"ticker={order.ticker} side={order.side} "
                f"qty={order.quantity} status={order.status}"
            )
            rows.append(AuditRow("A3", "FAIL", order.idempotency_key, detail))


def _audit_flags(graph: GraphStore, rows: list[AuditRow]) -> None:
    count = sum(
        1
        for node in graph.list_nodes("Flag")
        if str(node.props.get("status", "pending")) not in {"acknowledged", "resolved"}
    )
    rows.append(AuditRow("A4", "INFO", "unacknowledged_flags", str(count)))


def _active_positions_by_ticker(graph: GraphStore) -> dict[str, tuple[Node, ...]]:
    grouped: dict[str, list[Node]] = {}
    for node in graph.list_nodes("Position"):
        if is_active_position_node(node):
            grouped.setdefault(str(node.props.get("ticker", "")), []).append(node)
    return {ticker: tuple(nodes) for ticker, nodes in grouped.items() if ticker}


def _broker_quantities(positions: tuple[BrokerPosition, ...]) -> dict[str, int]:
    return {
        position.ticker: position.quantity
        for position in positions
        if position.quantity > 0
    }


def _pending_stop_quantities(orders: tuple[BrokerFill, ...]) -> dict[str, int]:
    quantities: dict[str, int] = {}
    for order in orders:
        if is_stop_order(order) and order.side == "sell" and order.status == "pending":
            quantities[order.ticker] = quantities.get(order.ticker, 0) + order.quantity
    return quantities


def _pending_closing_sell_quantities(orders: tuple[BrokerFill, ...]) -> dict[str, int]:
    quantities: dict[str, int] = {}
    for order in orders:
        if (
            not order.idempotency_key.startswith("stop:")
            and order.side == "sell"
            and order.status == "pending"
        ):
            quantities[order.ticker] = quantities.get(order.ticker, 0) + order.quantity
    return quantities


def _allowlist_reason(client_order_id: str) -> str | None:
    for prefix, reason in _ALLOWLIST.items():
        if client_order_id.startswith(prefix):
            return reason
    return None
