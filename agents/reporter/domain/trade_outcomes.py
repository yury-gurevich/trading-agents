"""Reporter trade-outcome metrics (profit-factor and expectancy).

Agent: reporter
Role: compute dollar-based profit-factor and expectancy from realized close PnL.
External I/O: none.

Reads the realized ``pnl_cents`` the monitor records on each CloseDecision (gross,
integer cents, for every trigger — stop, target, AND time). A close with no
``pnl_cents`` (a legacy node, or a hold, which writes no CloseDecision) is skipped.
This replaces the earlier trigger-derived percentage approximation, which had to
exclude time exits and assume exit-at-threshold.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel import Node

ZERO = 0.0


def collect_trade_outcomes(close_decisions: tuple[Node, ...]) -> dict[str, float]:
    """Collect dollar-based profit-factor and expectancy from realized close PnL."""
    pnls = [cents for cd in close_decisions if (cents := _pnl_cents(cd)) is not None]
    wins = sum(pnl for pnl in pnls if pnl > 0)
    losses = -sum(pnl for pnl in pnls if pnl < 0)  # positive gross loss magnitude
    return {
        "profit_factor": (wins / losses) if losses > 0 else ZERO,
        "expectancy_cents": (sum(pnls) / len(pnls)) if pnls else ZERO,
        "closed_trades_with_pnl": float(len(pnls)),
    }


def _pnl_cents(close_decision: Node) -> int | None:
    """Read the realized integer-cents PnL off a close decision; None when absent."""
    value = close_decision.props.get("pnl_cents")
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value
