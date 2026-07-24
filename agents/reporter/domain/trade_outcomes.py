"""Reporter trade-outcome metrics (profit-factor and expectancy).

Agent: reporter
Role: compute dollar-based profit-factor and expectancy from realized close PnL.
External I/O: none.

Reads realized ``realized_pnl_cents`` from execution Fill records. Historical
CloseDecision PnL remains legacy evidence only when it was not invalidated. When
no realized PnL evidence exists, uncomputable metric keys are omitted instead of
rendered as confident zeroes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel import Node


def collect_trade_outcomes(
    fills: tuple[Node, ...], close_decisions: tuple[Node, ...] = ()
) -> dict[str, float]:
    """Collect dollar-based profit-factor and expectancy from realized close PnL."""
    pnls = [
        cents
        for node in (*fills, *close_decisions)
        if (cents := _pnl_cents(node)) is not None
    ]
    if not pnls:
        return {"closed_trades_with_pnl": 0.0}
    wins = sum(pnl for pnl in pnls if pnl > 0)
    losses = -sum(pnl for pnl in pnls if pnl < 0)  # positive gross loss magnitude
    return {
        "profit_factor": (wins / losses) if losses > 0 else 0.0,
        "expectancy_cents": sum(pnls) / len(pnls),
        "closed_trades_with_pnl": float(len(pnls)),
    }


def _pnl_cents(node: Node) -> int | None:
    """Read realized integer-cents PnL from fill-first evidence."""
    if "pnl_invalidated_at" in node.props:
        return None
    value = node.props.get("realized_pnl_cents", node.props.get("pnl_cents"))
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value
