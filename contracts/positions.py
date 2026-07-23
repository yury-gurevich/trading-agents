"""Shared graph view of open Position nodes.

Agent: contracts
Role: define the cross-agent read model for currently held tickers.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contracts.common import Ticker
    from kernel import GraphStore, Node

POSITION_LABEL = "Position"
_CLOSES_EDGE = "CLOSES"


@dataclass(frozen=True)
class OpenPosition:
    """Active position quantity read from the graph."""

    ticker: Ticker
    quantity: int


def active_position_nodes(graph: GraphStore) -> tuple[Node, ...]:
    """Return open Position nodes not superseded by broker reconciliation."""
    return tuple(
        node
        for node in graph.list_nodes(POSITION_LABEL)
        if _broker_active(node) and _is_open_position(graph, node)
    )


def open_positions(graph: GraphStore) -> tuple[OpenPosition, ...]:
    """Return open held tickers with quantities aggregated by ticker."""
    quantities: dict[Ticker, int] = {}
    for node in active_position_nodes(graph):
        ticker = str(node.props["ticker"])
        quantities[ticker] = quantities.get(ticker, 0) + int(node.props["quantity"])
    return tuple(
        OpenPosition(ticker=ticker, quantity=quantity)
        for ticker, quantity in sorted(quantities.items())
    )


def open_position_tickers(graph: GraphStore) -> tuple[Ticker, ...]:
    """Return active held tickers in stable order."""
    return tuple(position.ticker for position in open_positions(graph))


def _broker_active(node: Node) -> bool:
    if node.props.get("status", "open") != "open":
        return False
    return not (
        node.props.get("broker_absent") or node.props.get("broker_superseded_by")
    )


def _is_open_position(graph: GraphStore, position: Node) -> bool:
    closes = graph.ancestors(position, max_depth=1, edge_types={_CLOSES_EDGE})
    return not any(close.props.get("decision") == "close" for close in closes)
