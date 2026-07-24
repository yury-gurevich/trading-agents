"""Shared graph view of open Position nodes.

Agent: contracts
Role: define the cross-agent read model for currently held tickers.
External I/O: none.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contracts.common import Ticker
    from kernel import GraphStore, Node

POSITION_LABEL = "Position"


@dataclass(frozen=True)
class OpenPosition:
    """Active position quantity read from the graph."""

    ticker: Ticker
    quantity: int
    position_ref: str


@dataclass(frozen=True)
class PositionBasisLot:
    """One active position lot contributing to a sell intent."""

    node_key: str
    ticker: Ticker
    quantity: int
    opened_price_cents: int


@dataclass(frozen=True)
class PositionBasis:
    """Resolved basis for the position_ref carried by a sell OrderIntent."""

    ticker: Ticker
    position_ref: str
    lots: tuple[PositionBasisLot, ...]

    @property
    def quantity(self) -> int:
        """Return total active quantity represented by this basis."""
        return sum(lot.quantity for lot in self.lots)


@dataclass(frozen=True)
class PositionStopThreshold:
    """Aggregated stop threshold inputs for one active held ticker."""

    ticker: Ticker
    opened_price_cents: int
    stop_pct: float


def active_position_nodes(graph: GraphStore) -> tuple[Node, ...]:
    """Return open Position nodes not superseded by broker reconciliation."""
    return tuple(
        node
        for node in graph.list_nodes(POSITION_LABEL)
        if is_active_position_node(node)
    )


def open_positions(graph: GraphStore) -> tuple[OpenPosition, ...]:
    """Return open held tickers with quantities aggregated by ticker."""
    nodes_by_ticker = _active_nodes_by_ticker(graph)
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


def open_position_stop_thresholds(
    graph: GraphStore,
) -> tuple[PositionStopThreshold, ...]:
    """Return weighted stop inputs for active positions grouped by ticker."""
    return tuple(
        _stop_threshold(ticker, tuple(sorted(nodes, key=lambda node: node.key)))
        for ticker, nodes in sorted(_active_nodes_by_ticker(graph).items())
    )


def position_basis_for_ref(
    graph: GraphStore, *, position_ref: str, ticker: Ticker
) -> PositionBasis | None:
    """Resolve a sell intent's stable position_ref into active basis lots."""
    for current_ticker, nodes in _active_nodes_by_ticker(graph).items():
        if current_ticker != ticker:
            continue
        sorted_nodes = tuple(sorted(nodes, key=lambda node: node.key))
        if _position_ref(tuple(node.key for node in sorted_nodes)) != position_ref:
            return None
        lots = tuple(_basis_lot(node) for node in sorted_nodes)
        if any(lot is None for lot in lots):
            return None
        return PositionBasis(
            ticker=ticker,
            position_ref=position_ref,
            lots=tuple(lot for lot in lots if lot is not None),
        )
    return None


def is_active_position_node(node: Node) -> bool:
    """Return whether broker evidence still treats a Position as open."""
    if node.props.get("status", "open") != "open":
        return False
    return not (
        node.props.get("broker_absent") or node.props.get("broker_superseded_by")
    )


def _active_nodes_by_ticker(graph: GraphStore) -> dict[Ticker, list[Node]]:
    nodes_by_ticker: dict[Ticker, list[Node]] = {}
    for node in active_position_nodes(graph):
        ticker = str(node.props["ticker"])
        nodes_by_ticker.setdefault(ticker, []).append(node)
    return nodes_by_ticker


def _basis_lot(node: Node) -> PositionBasisLot | None:
    try:
        return PositionBasisLot(
            node_key=node.key,
            ticker=str(node.props["ticker"]),
            quantity=int(node.props["quantity"]),
            opened_price_cents=int(node.props["opened_price_cents"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _stop_threshold(ticker: Ticker, nodes: tuple[Node, ...]) -> PositionStopThreshold:
    lots = tuple(_stop_lot(ticker, node) for node in nodes)
    stop_pcts = {stop_pct for _quantity, _opened, stop_pct in lots}
    if len(stop_pcts) != 1:
        raise ValueError(f"active lots for {ticker} carry different stop_pct values")
    quantity = sum(lot_quantity for lot_quantity, _opened, _stop_pct in lots)
    if quantity <= 0:
        raise ValueError(f"active lots for {ticker} carry non-positive quantity")
    numerator = sum(opened * lot_quantity for lot_quantity, opened, _stop_pct in lots)
    opened = int(
        (Decimal(numerator) / Decimal(quantity)).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )
    return PositionStopThreshold(
        ticker=ticker,
        opened_price_cents=opened,
        stop_pct=next(iter(stop_pcts)),
    )


def _stop_lot(ticker: Ticker, node: Node) -> tuple[int, int, float]:
    try:
        return (
            int(node.props["quantity"]),
            int(node.props["opened_price_cents"]),
            float(node.props["stop_pct"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        message = f"active lot for {ticker} lacks stop threshold inputs"
        raise ValueError(message) from exc


def _position_ref(keys: tuple[str, ...]) -> str:
    joined = "\n".join(sorted(keys)).encode("utf-8")
    return hashlib.sha256(joined).hexdigest()[:16]
