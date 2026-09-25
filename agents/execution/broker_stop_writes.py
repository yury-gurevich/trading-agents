"""Graph facts written when a broker stop is placed.

Agent: execution
Role: append the stop Fill, the BrokerStopOrder fact, and its position edges.
External I/O: injected GraphStore writes.

Split out of broker_stop_actions.py by S225, which was about to push that module
past the 150-line warning line while adding the `derived_from` provenance field.
Imports run one way only - this module never imports its caller (DL-198).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from agents.execution.fill_attempts import fill_attempt_chain, select_fill_attempt
from contracts.broker_stops import BROKER_STOP_ORDER_LABEL
from contracts.positions import active_position_nodes, position_basis_for_ref

if TYPE_CHECKING:
    from agents.execution.broker import BrokerFill
    from agents.execution.broker_stop_types import StopProvenance
    from contracts.broker_stops import BrokerStopOrder
    from contracts.positions import PositionStopThreshold
    from kernel import GraphStore, Node

PROTECTED_BY_EDGE = "PROTECTED_BY"
STOP_FILL_EDGE = "STOPS_WITH"


def write_stop_fill(
    graph: GraphStore,
    threshold: PositionStopThreshold,
    key: str,
    fill: BrokerFill,
    stop_cents: int,
    *,
    provenance: StopProvenance,
) -> Node:
    """Append the stop submission attempt as an execution-owned Fill."""
    props = {
        "ticker": threshold.ticker,
        "side": "sell",
        "quantity": threshold.quantity,
        "price_cents": stop_cents,
        "price_currency": fill.price.currency,
        "broker_order_id": fill.broker_order_id,
        "status": fill.status,
        "reason": fill.reason,
        "position_ref": threshold.position_ref,
        "stop_order_key": key,
        "stop_pct": threshold.stop_pct,
        "stop_pct_source": provenance.stop_pct_source,
        "derived_from": provenance.derived_from,
    }
    attempt = select_fill_attempt(
        graph,
        key,
        props,
        force_new=fill.status == "rejected" and bool(fill_attempt_chain(graph, key)),
    )
    return graph.merge_node("Fill", attempt.key, attempt.props)


def write_stop_order(
    graph: GraphStore,
    threshold: PositionStopThreshold,
    key: str,
    fill: BrokerFill,
    stop_cents: int,
    *,
    provenance: StopProvenance,
    replaces: BrokerStopOrder | None = None,
) -> Node:
    """Append the immutable BrokerStopOrder fact for a placed or replacing stop."""
    props: dict[str, object] = {
        "ticker": threshold.ticker,
        "position_ref": threshold.position_ref,
        "stop_price_cents": stop_cents,
        "stop_pct": threshold.stop_pct,
        "stop_pct_source": provenance.stop_pct_source,
        "derived_from": provenance.derived_from,
        "broker_order_id": fill.broker_order_id,
        "placed_at": datetime.now(tz=UTC).isoformat(),
    }
    if replaces is not None:
        props["replaces"] = replaces.key
        props["replaces_broker_order_id"] = replaces.broker_order_id
    return graph.merge_node(BROKER_STOP_ORDER_LABEL, key, props)


def mark_replaced(graph: GraphStore, old: BrokerStopOrder, new: Node) -> None:
    """Append the replacement marker to the old fact; it is never deleted."""
    graph.merge_node(
        BROKER_STOP_ORDER_LABEL,
        old.key,
        {
            "replaced_at": datetime.now(tz=UTC).isoformat(),
            "replaced_by": new.key,
            "replaced_by_broker_order_id": new.props["broker_order_id"],
        },
    )


def link_positions(
    graph: GraphStore, threshold: PositionStopThreshold, stop: Node
) -> None:
    """Edge every active lot in the stop's basis to the stop that protects it."""
    basis = position_basis_for_ref(
        graph, position_ref=threshold.position_ref, ticker=threshold.ticker
    )
    if basis is None:
        return
    by_key = {node.key: node for node in active_position_nodes(graph)}
    for lot in basis.lots:
        position = by_key.get(lot.node_key)
        if position is not None:
            graph.add_edge(position, stop, PROTECTED_BY_EDGE)
