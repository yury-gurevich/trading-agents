"""Shared graph view of open Position nodes.

Agent: contracts
Role: define the cross-agent read model for currently held tickers.
External I/O: none.
"""

from __future__ import annotations

import hashlib
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
    position_ref: str


def active_position_nodes(graph: GraphStore) -> tuple[Node, ...]:
    """Return open Position nodes not superseded by broker reconciliation."""
    return tuple(
        node
        for node in graph.list_nodes(POSITION_LABEL)
        if _broker_active(node) and _is_open_position(graph, node)
    )


def open_positions(graph: GraphStore) -> tuple[OpenPosition, ...]:
    """Return open held tickers with quantities aggregated by ticker."""
    nodes_by_ticker: dict[Ticker, list[Node]] = {}
    for node in active_position_nodes(graph):
        ticker = str(node.props["ticker"])
        nodes_by_ticker.setdefault(ticker, []).append(node)
    return tuple(
        OpenPosition(
            ticker=ticker,
            quantity=sum(int(node.props["quantity"]) for node in nodes),
            position_ref=_position_ref(tuple(node.key for node in nodes)),
        )
        for ticker, nodes in sorted(nodes_by_ticker.items())
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


def _position_ref(keys: tuple[str, ...]) -> str:
    joined = "\n".join(sorted(keys)).encode("utf-8")
    return hashlib.sha256(joined).hexdigest()[:16]
