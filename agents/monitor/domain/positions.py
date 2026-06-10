"""Position reconstruction from execution fills.

Agent: monitor
Role: derive stable position properties from Fill and OrderIntent graph lineage.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from agents.monitor.domain.exit_rules import ExitPosition

if TYPE_CHECKING:
    from kernel import GraphStore, Node


@dataclass(frozen=True)
class PositionDraft:
    """Position fields ready for monitor graph storage."""

    run_id: str
    ticker: str
    opened_price_cents: int
    quantity: int
    stop_pct: float
    target_pct: float
    horizon_days: int
    opened_at: str
    degraded: bool = False


def position_from_fill(
    graph: GraphStore,
    *,
    run_id: str,
    fill: Node,
    default_stop_pct: float,
    default_target_pct: float,
    default_horizon_days: int,
) -> PositionDraft:
    """Build a position draft from a Fill node and its OrderIntent lineage."""
    order = _order_intent(graph, fill)
    stop_pct, target_pct, degraded = _stop_target(
        order,
        default_stop_pct=default_stop_pct,
        default_target_pct=default_target_pct,
    )
    return PositionDraft(
        run_id=run_id,
        ticker=str(fill.props["ticker"]),
        opened_price_cents=int(fill.props["price_cents"]),
        quantity=int(fill.props["quantity"]),
        stop_pct=stop_pct,
        target_pct=target_pct,
        horizon_days=default_horizon_days,
        opened_at=datetime.now(tz=UTC).isoformat(),
        degraded=degraded,
    )


def exit_position(node: Node) -> ExitPosition:
    """Return an exit-rule position object from a stored graph node."""
    return ExitPosition(
        opened_price_cents=int(node.props["opened_price_cents"]),
        opened_at=str(node.props["opened_at"]),
        stop_pct=float(node.props["stop_pct"]),
        target_pct=float(node.props["target_pct"]),
        horizon_days=int(node.props["horizon_days"]),
    )


def _order_intent(graph: GraphStore, fill: Node) -> Node | None:
    orders = tuple(graph.descendants(fill, max_depth=1, edge_types={"EXECUTES"}))
    return orders[0] if orders else None


def _stop_target(
    order: Node | None, *, default_stop_pct: float, default_target_pct: float
) -> tuple[float, float, bool]:
    if order is None:
        return default_stop_pct, default_target_pct, True
    stop = order.props.get("stop_pct")
    target = order.props.get("target_pct")
    return (
        default_stop_pct if stop is None else float(stop),
        default_target_pct if target is None else float(target),
        stop is None or target is None,
    )
