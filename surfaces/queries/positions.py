"""Position read models.

Agent: surfaces
Role: project position lifecycle state from graph nodes and close edges.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from surfaces.queries._graph import nodes_by_label

if TYPE_CHECKING:
    from kernel import GraphStore, Node


@dataclass(frozen=True)
class PositionView:
    """Operator-facing view of one position."""

    position_id: str
    ticker: str
    quantity: int
    opened_price_cents: int
    status: str
    close_trigger: str | None


def open_positions(graph: GraphStore) -> tuple[PositionView, ...]:
    """Return all Position nodes that have no linked CloseDecision."""
    return tuple(
        sorted(
            (
                _view(graph, node)
                for node in nodes_by_label(graph, "Position")
                if _is_open(graph, node)
            ),
            key=lambda item: (item.ticker, item.position_id),
        )
    )


def positions_for_run(graph: GraphStore, run_id: str) -> tuple[PositionView, ...]:
    """Return Position nodes opened by a specific PM run."""
    return tuple(
        sorted(
            (
                _view(graph, node)
                for node in nodes_by_label(graph, "Position")
                if str(node.props.get("run_id", "")) == run_id
            ),
            key=lambda item: (item.ticker, item.position_id),
        )
    )


def _view(graph: GraphStore, node: Node) -> PositionView:
    close = _close_decision(graph, node)
    return PositionView(
        position_id=node.key,
        ticker=str(node.props.get("ticker", "")),
        quantity=int(node.props.get("quantity", 0)),
        opened_price_cents=int(node.props.get("opened_price_cents", 0)),
        status="closed" if close is not None else str(node.props.get("status", "open")),
        close_trigger=None if close is None else str(close.props.get("trigger", "")),
    )


def _is_open(graph: GraphStore, node: Node) -> bool:
    return node.props.get("status") != "closed" and _close_decision(graph, node) is None


def _close_decision(graph: GraphStore, node: Node) -> Node | None:
    for close in graph.ancestors(node, max_depth=1, edge_types={"CLOSES"}):
        if close.label == "CloseDecision":
            return close
    return None
