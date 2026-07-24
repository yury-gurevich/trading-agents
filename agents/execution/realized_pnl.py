"""Realized PnL derivation for broker-confirmed sell fills.

Agent: execution
Role: append fill-time realized PnL only when entry basis is resolvable.
External I/O: GraphStore writes only through the caller's append path.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.pnl import realized_pnl_cents
from contracts.positions import PositionBasis, position_basis_for_ref
from kernel import AgentFault

if TYPE_CHECKING:
    from agents.execution.broker import BrokerFill
    from kernel import FaultSink, GraphStore, Node

REALIZED_PNL_PROP = "realized_pnl_cents"
_EXECUTES_EDGE = "EXECUTES"
_REALIZED_STATUSES = {"filled", "partial"}


def realized_pnl_props(
    graph: GraphStore,
    fill_node: Node,
    broker_fill: BrokerFill,
    sink: FaultSink,
    *,
    exit_price_cents: int,
) -> dict[str, object]:
    """Return realized-PnL props for a broker-confirmed sell fill, or record a Fault."""
    if not _needs_realized_pnl(fill_node, broker_fill):
        return {}
    position_ref = _position_ref_from_order(graph, fill_node)
    if position_ref is None:
        _record_unresolved(sink, fill_node, broker_fill, "missing position_ref")
        return {}
    basis = position_basis_for_ref(
        graph, position_ref=position_ref, ticker=broker_fill.ticker
    )
    pnl = _pnl_from_basis(basis, broker_fill.quantity, exit_price_cents)
    if pnl is None:
        _record_unresolved(sink, fill_node, broker_fill, "entry basis unresolved")
        return {}
    return {REALIZED_PNL_PROP: pnl}


def _needs_realized_pnl(fill_node: Node, broker_fill: BrokerFill) -> bool:
    return (
        broker_fill.side == "sell"
        and broker_fill.status in _REALIZED_STATUSES
        and REALIZED_PNL_PROP not in fill_node.props
    )


def _position_ref_from_order(graph: GraphStore, fill_node: Node) -> str | None:
    order = next(
        iter(graph.descendants(fill_node, max_depth=1, edge_types={_EXECUTES_EDGE})),
        None,
    )
    value = None if order is None else order.props.get("position_ref")
    return value if isinstance(value, str) and value else None


def _pnl_from_basis(
    basis: PositionBasis | None, quantity: int, exit_price_cents: int
) -> int | None:
    if basis is None or quantity <= 0 or quantity > basis.quantity:
        return None
    entry_prices = {lot.opened_price_cents for lot in basis.lots}
    if len(entry_prices) == 1:
        return realized_pnl_cents(
            exit_price_cents, basis.lots[0].opened_price_cents, quantity
        )
    if quantity == basis.quantity:
        return sum(
            realized_pnl_cents(exit_price_cents, lot.opened_price_cents, lot.quantity)
            for lot in basis.lots
        )
    return None


def _record_unresolved(
    sink: FaultSink, fill_node: Node, broker_fill: BrokerFill, reason: str
) -> None:
    sink.submit(
        AgentFault(
            source_agent="execution",
            source_module="agents.execution.realized_pnl",
            capability="refresh_pending_fills",
            error_type="UnresolvedEntryBasis",
            message=(
                "realized PnL skipped for "
                f"{broker_fill.ticker} sell fill {fill_node.key}: {reason}"
            ),
            context={
                "fill_key": fill_node.key,
                "ticker": broker_fill.ticker,
                "broker_order_id": broker_fill.broker_order_id,
                "quantity": broker_fill.quantity,
            },
        )
    )
