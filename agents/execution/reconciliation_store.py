"""Graph writes and comparisons for execution broker reconciliation.

Agent: execution
Role: persist broker snapshots, refresh pending fills, and describe position drift.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING, Literal

from agents.execution.order_status_store import write_order_status
from contracts.positions import is_active_position_node

if TYPE_CHECKING:
    from agents.execution.broker import BrokerFill, BrokerPosition
    from kernel import GraphStore, Node

SnapshotStatus = Literal["fresh", "stale"]

_CENTS = Decimal("100")
_ONE = Decimal("1")


def refresh_pending_fills(
    graph: GraphStore, broker_fills: tuple[BrokerFill, ...]
) -> None:
    """Append broker terminal-status evidence to pending Fill nodes."""
    by_key = {fill.idempotency_key: fill for fill in broker_fills}
    by_order_id = {
        fill.broker_order_id: fill for fill in broker_fills if fill.broker_order_id
    }
    for node in graph.list_nodes("Fill"):
        if node.props.get("status") != "pending":
            continue
        broker_fill = by_key.get(node.key) or by_order_id.get(
            str(node.props.get("broker_order_id", ""))
        )
        if broker_fill is None:
            continue
        write_order_status(graph, fill_node=node, broker_fill=broker_fill)
        if broker_fill.status == "pending" or "broker_status" in node.props:
            continue
        props: dict[str, object] = {
            "broker_status": broker_fill.status,
            "broker_status_broker_order_id": broker_fill.broker_order_id,
            "broker_status_refreshed_at": datetime.now(tz=UTC).isoformat(),
        }
        if broker_fill.status in ("filled", "partial"):
            props["broker_price_cents"] = _money_to_cents(broker_fill)
        graph.merge_node("Fill", node.key, props)


def write_snapshot(
    graph: GraphStore,
    *,
    run_id: str,
    holdings: tuple[BrokerPosition, ...],
    status: SnapshotStatus,
    stale_reason: str | None,
) -> Node:
    """Append one broker-position snapshot node."""
    created_at = datetime.now(tz=UTC).isoformat()
    props: dict[str, object] = {
        "run_id": run_id,
        "status": status,
        "created_at": created_at,
        "holding_count": len(holdings),
        "holdings": [_holding_props(position) for position in holdings],
    }
    if stale_reason is not None:
        props["stale_reason"] = stale_reason
    return graph.merge_node(
        "BrokerPositionSnapshot",
        f"broker-position-snapshot:{run_id}:{created_at}",
        props,
    )


def position_divergences(
    graph: GraphStore, positions: tuple[BrokerPosition, ...]
) -> tuple[str, ...]:
    """Compare active graph positions with broker holdings by ticker quantity."""
    broker_qty = {position.ticker: position.quantity for position in positions}
    graph_qty = _graph_position_quantities(graph)
    divergences: list[str] = []
    for ticker in sorted(set(broker_qty) - set(graph_qty)):
        divergences.append(
            f"missing_graph_position {ticker} broker_qty={broker_qty[ticker]}"
        )
    for ticker in sorted(set(graph_qty) - set(broker_qty)):
        divergences.append(
            f"extra_graph_position {ticker} graph_qty={graph_qty[ticker]}"
        )
    for ticker in sorted(set(broker_qty) & set(graph_qty)):
        if graph_qty[ticker] != broker_qty[ticker]:
            divergences.append(
                f"qty_mismatch {ticker} "
                f"graph_qty={graph_qty[ticker]} broker_qty={broker_qty[ticker]}"
            )
    return tuple(divergences)


def write_divergence_flag(
    graph: GraphStore, *, snapshot: Node, divergences: tuple[str, ...]
) -> None:
    """Write the supervisor-shaped Flag requested by DL-44."""
    subject_ref = f"broker-position-divergence:{snapshot.key}"
    key = f"flag:{subject_ref}:critical"
    if graph.get_node("Flag", key) is not None:
        return
    graph.merge_node(
        "Flag",
        key,
        {
            "subject_ref": subject_ref,
            "severity": "critical",
            "reason": _flag_reason(snapshot, divergences),
            "status": "pending",
            "created_at": datetime.now(tz=UTC).isoformat(),
        },
    )


def _holding_props(position: BrokerPosition) -> dict[str, object]:
    return {
        "ticker": position.ticker,
        "quantity": position.quantity,
        "avg_entry_cents": position.avg_entry_cents,
        "market_value_cents": position.market_value_cents,
    }


def _graph_position_quantities(graph: GraphStore) -> dict[str, int]:
    quantities: dict[str, int] = {}
    for node in graph.list_nodes("Position"):
        if not _is_active_position(graph, node):
            continue
        ticker = str(node.props["ticker"])
        quantities[ticker] = quantities.get(ticker, 0) + int(node.props["quantity"])
    return quantities


def _is_active_position(graph: GraphStore, node: Node) -> bool:
    del graph
    return is_active_position_node(node)


def _flag_reason(snapshot: Node, divergences: tuple[str, ...]) -> str:
    lines = "\n".join(f"- {item}" for item in divergences)
    return f"Broker position divergence at run start ({snapshot.key}):\n{lines}"


def _money_to_cents(fill: BrokerFill) -> int:
    cents = (fill.price.amount * _CENTS).quantize(_ONE, rounding=ROUND_HALF_UP)
    return int(cents)
