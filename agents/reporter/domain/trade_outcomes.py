"""Reporter trade-outcome metrics (profit-factor and expectancy).

Agent: reporter
Role: compute profit-factor and expectancy from paired Position and CloseDecision nodes.
External I/O: none.

Note: time-triggered exits are excluded because their implied pnl requires the exit
price from PositionCheck (a separate graph node not in scope here); only stop- and
target-triggered closes contribute to these metrics. The paper broker exits at the
trigger price, so a stop close implies pnl_pct == -stop_pct and a target close implies
pnl_pct == +target_pct, both read directly off the Position node.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel import Node

ZERO = 0.0


def collect_trade_outcomes(
    positions: tuple[Node, ...], close_decisions: tuple[Node, ...]
) -> dict[str, float]:
    """Collect profit-factor and expectancy from paired position + close nodes."""
    by_position = {
        cd.props["position_id"]: cd
        for cd in close_decisions
        if "position_id" in cd.props
    }
    wins: list[float] = []
    losses: list[float] = []
    for position in positions:
        close = by_position.get(position.key)
        if close is None:
            continue
        pnl = _implied_pnl_pct(position, close)
        if pnl is None:
            continue
        bucket = wins if close.props.get("trigger") == "target" else losses
        bucket.append(pnl)
    return _summarise(wins, losses)


def _summarise(wins: list[float], losses: list[float]) -> dict[str, float]:
    loss_sum = -sum(losses)  # losses are signed negative; gross loss is positive
    pnls = wins + losses
    return {
        "profit_factor": (sum(wins) / loss_sum) if loss_sum > ZERO else ZERO,
        "expectancy_pct": (sum(pnls) / len(pnls)) if pnls else ZERO,
        "closed_trades_with_pnl": float(len(pnls)),
    }


def _implied_pnl_pct(position: Node, close_decision: Node) -> float | None:
    trigger = close_decision.props.get("trigger")
    if trigger == "stop":
        return -_pct(position, "stop_pct")
    if trigger == "target":
        return _pct(position, "target_pct")
    return None


def _pct(node: Node, prop: str) -> float:
    try:
        return float(node.props.get(prop, ZERO))
    except (TypeError, ValueError):
        return ZERO
