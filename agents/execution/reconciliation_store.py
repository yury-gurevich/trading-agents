"""Graph writes and comparisons for execution broker reconciliation.

Agent: execution
Role: persist broker snapshots, refresh pending fills, and describe position drift.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal, NamedTuple

from agents.execution.broker_status_refresh import (
    broker_price_cents,
    broker_status_props,
    exit_price_cents,
)
from agents.execution.fill_attempts import broker_idempotency_key
from agents.execution.order_status_store import write_order_status
from agents.execution.realized_pnl import realized_pnl_props
from agents.execution.snapshot_account import account_snapshot_props
from contracts.positions import is_active_position_node

if TYPE_CHECKING:
    from agents.execution.broker import BrokerAccount, BrokerFill, BrokerPosition
    from kernel import FaultSink, GraphStore, Node

SnapshotStatus = Literal["fresh", "stale"]

_TERMINAL_BROKER_STATUSES = frozenset({"filled", "rejected"})


def refresh_pending_fills(
    graph: GraphStore, broker_fills: tuple[BrokerFill, ...], sink: FaultSink
) -> None:
    """Append broker terminal-status evidence to pending Fill nodes."""
    by_key = {fill.idempotency_key: fill for fill in broker_fills}
    by_order_id = {
        fill.broker_order_id: fill for fill in broker_fills if fill.broker_order_id
    }
    for node in graph.list_nodes("Fill"):
        if node.props.get("status") != "pending":
            continue
        if node.props.get("broker_status") in _TERMINAL_BROKER_STATUSES:
            continue
        broker_fill = by_key.get(broker_idempotency_key(node)) or by_order_id.get(
            str(node.props.get("broker_order_id", ""))
        )
        if broker_fill is None:
            continue
        write_order_status(graph, fill_node=node, broker_fill=broker_fill)
        if broker_fill.status == "pending":
            continue
        current_price_cents = broker_price_cents(broker_fill)
        exit_cents = exit_price_cents(node, broker_fill, current_price_cents)
        props = broker_status_props(node, broker_fill, current_price_cents)
        props.update(
            realized_pnl_props(
                graph,
                node,
                broker_fill,
                sink,
                exit_price_cents=exit_cents,
            )
        )
        if props:
            graph.merge_node("Fill", node.key, props)


def write_snapshot(
    graph: GraphStore,
    *,
    run_id: str,
    holdings: tuple[BrokerPosition, ...],
    account: BrokerAccount | None,
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
    props.update(account_snapshot_props(account, stale_reason))
    if stale_reason is not None:
        props["stale_reason"] = stale_reason
    return graph.merge_node(
        "BrokerPositionSnapshot",
        f"broker-position-snapshot:{run_id}:{created_at}",
        props,
    )


class Divergence(NamedTuple):
    """One graph-vs-broker disagreement, with an identity stable across runs."""

    kind: str
    ticker: str
    detail: str

    @property
    def text(self) -> str:
        """Human-readable one-line form used in Flag reasons."""
        return f"{self.kind} {self.ticker} {self.detail}"


def position_divergences(
    graph: GraphStore, positions: tuple[BrokerPosition, ...]
) -> tuple[Divergence, ...]:
    """Compare active graph positions with broker holdings by ticker quantity."""
    broker_qty = {position.ticker: position.quantity for position in positions}
    graph_qty = _graph_position_quantities(graph)
    divergences: list[Divergence] = []
    for ticker in sorted(set(broker_qty) - set(graph_qty)):
        divergences.append(
            Divergence(
                "missing_graph_position", ticker, f"broker_qty={broker_qty[ticker]}"
            )
        )
    for ticker in sorted(set(graph_qty) - set(broker_qty)):
        divergences.append(
            Divergence("extra_graph_position", ticker, f"graph_qty={graph_qty[ticker]}")
        )
    for ticker in sorted(set(broker_qty) & set(graph_qty)):
        if graph_qty[ticker] != broker_qty[ticker]:
            divergences.append(
                Divergence(
                    "qty_mismatch",
                    ticker,
                    f"graph_qty={graph_qty[ticker]} broker_qty={broker_qty[ticker]}",
                )
            )
    return tuple(divergences)


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
