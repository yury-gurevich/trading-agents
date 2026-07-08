"""Broker-snapshot adoption for monitor-owned Position nodes.

Agent: monitor
Role: reconcile Position nodes from execution's BrokerPositionSnapshot seam.
External I/O: none.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

from agents.monitor.position_book import active_positions

if TYPE_CHECKING:
    from agents.monitor.settings import MonitorSettings
    from kernel import GraphStore, Node

_SNAPSHOT_LABEL = "BrokerPositionSnapshot"


@dataclass(frozen=True)
class SnapshotHolding:
    """One holding row from a BrokerPositionSnapshot."""

    ticker: str
    quantity: int
    avg_entry_cents: int
    market_value_cents: int


def reconcile_positions_from_latest_snapshot(
    graph: GraphStore, settings: MonitorSettings
) -> None:
    """Adopt broker holdings into monitor-owned Position nodes."""
    snapshot = _latest_fresh_snapshot(graph)
    if snapshot is None:
        return
    holdings = _holdings(snapshot)
    active_by_ticker = _positions_by_ticker(active_positions(graph))
    held_tickers = {holding.ticker for holding in holdings}
    for holding in holdings:
        candidates = active_by_ticker.get(holding.ticker, ())
        match = _matching_position(candidates, holding)
        if match is None:
            match = _create_broker_position(graph, snapshot, holding, settings)
        for node in candidates:
            if node.key != match.key:
                _mark_superseded(graph, node, match, snapshot)
    for ticker, nodes in active_by_ticker.items():
        if ticker not in held_tickers:
            for node in nodes:
                _mark_absent(graph, node, snapshot)


def _latest_fresh_snapshot(graph: GraphStore) -> Node | None:
    snapshots = [
        node
        for node in graph.list_nodes(_SNAPSHOT_LABEL)
        if node.props.get("status") == "fresh"
    ]
    if not snapshots:
        return None
    return max(snapshots, key=lambda node: str(node.props.get("created_at", "")))


def _holdings(snapshot: Node) -> tuple[SnapshotHolding, ...]:
    rows: list[SnapshotHolding] = []
    for item in snapshot.props.get("holdings", ()):
        if not isinstance(item, Mapping):
            continue
        rows.append(
            SnapshotHolding(
                ticker=str(item.get("ticker", "")),
                quantity=int(item.get("quantity", 0)),
                avg_entry_cents=int(item.get("avg_entry_cents", 0)),
                market_value_cents=int(item.get("market_value_cents", 0)),
            )
        )
    return tuple(row for row in rows if row.ticker and row.quantity > 0)


def _positions_by_ticker(nodes: tuple[Node, ...]) -> dict[str, tuple[Node, ...]]:
    grouped: dict[str, list[Node]] = {}
    for node in nodes:
        grouped.setdefault(str(node.props["ticker"]), []).append(node)
    return {ticker: tuple(items) for ticker, items in grouped.items()}


def _matching_position(
    candidates: tuple[Node, ...], holding: SnapshotHolding
) -> Node | None:
    for node in candidates:
        if int(node.props["quantity"]) != holding.quantity:
            continue
        if int(node.props["opened_price_cents"]) == holding.avg_entry_cents:
            return node
    return None


def _create_broker_position(
    graph: GraphStore,
    snapshot: Node,
    holding: SnapshotHolding,
    settings: MonitorSettings,
) -> Node:
    key = f"broker:{holding.ticker}:{holding.quantity}:{holding.avg_entry_cents}"
    current = graph.get_node("Position", key)
    if current is not None:
        return current
    return graph.merge_node(
        "Position",
        key,
        {
            "run_id": snapshot.props["run_id"],
            "ticker": holding.ticker,
            "opened_price_cents": holding.avg_entry_cents,
            "quantity": holding.quantity,
            "stop_pct": settings.default_stop_pct,
            "target_pct": settings.default_target_pct,
            "horizon_days": settings.default_horizon_days,
            "opened_at": snapshot.props["created_at"],
            "status": "open",
            "degraded": True,
            "provenance": "reconciled-from-broker",
            "source_snapshot": snapshot.key,
            "broker_market_value_cents": holding.market_value_cents,
        },
    )


def _mark_superseded(
    graph: GraphStore, node: Node, replacement: Node, snapshot: Node
) -> None:
    if "broker_superseded_by" not in node.props:  # pragma: no branch
        graph.merge_node(
            "Position",
            node.key,
            {
                "broker_superseded_by": replacement.key,
                "broker_superseded_snapshot": snapshot.key,
            },
        )


def _mark_absent(graph: GraphStore, node: Node, snapshot: Node) -> None:
    if "broker_absent" not in node.props:  # pragma: no branch
        graph.merge_node(
            "Position",
            node.key,
            {"broker_absent": True, "broker_absent_snapshot": snapshot.key},
        )
