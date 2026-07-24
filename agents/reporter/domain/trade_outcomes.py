"""Reporter trade-outcome metrics (profit-factor and expectancy).

Agent: reporter
Role: compute dollar-based profit-factor and expectancy from realized close PnL.
External I/O: none.

Reads realized ``pnl_cents`` from historical close records until execution records
fill-time PnL. Close decisions marked with ``pnl_invalidated_at`` are skipped.
When no realized PnL evidence exists, uncomputable metric keys are omitted instead
of rendered as confident zeroes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel import Node


def collect_trade_outcomes(close_decisions: tuple[Node, ...]) -> dict[str, float]:
    """Collect dollar-based profit-factor and expectancy from realized close PnL."""
    pnls = [cents for cd in close_decisions if (cents := _pnl_cents(cd)) is not None]
    if not pnls:
        return {"closed_trades_with_pnl": 0.0}
    wins = sum(pnl for pnl in pnls if pnl > 0)
    losses = -sum(pnl for pnl in pnls if pnl < 0)  # positive gross loss magnitude
    return {
        "profit_factor": (wins / losses) if losses > 0 else 0.0,
        "expectancy_cents": sum(pnls) / len(pnls),
        "closed_trades_with_pnl": float(len(pnls)),
    }


def _pnl_cents(close_decision: Node) -> int | None:
    """Read the realized integer-cents PnL off a close decision; None when absent."""
    if "pnl_invalidated_at" in close_decision.props:
        return None
    value = close_decision.props.get("pnl_cents")
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value
