"""Reporter metric reducers.

Agent: reporter
Role: turn provenance graph nodes into run-level numeric metric dictionaries.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel import Node

ZERO = 0.0


def collect_portfolio_metrics(
    pm_run: Node | None,
    positions: tuple[Node, ...],
    close_decisions: tuple[Node, ...],
) -> dict[str, float]:
    """Collect position and PM approval metrics for one PM run."""
    approved = _number(pm_run, "approved_count")
    rejected = _number(pm_run, "rejected_count")
    closed = float(len(close_decisions))
    opened = float(len(positions))
    total_decisions = approved + rejected
    return {
        "positions_opened": opened,
        "positions_closed": closed,
        "positions_held": max(opened - closed, ZERO),
        "close_trigger_stop": _trigger_count(close_decisions, "stop"),
        "close_trigger_target": _trigger_count(close_decisions, "target"),
        "close_trigger_time": _trigger_count(close_decisions, "time"),
        "approval_rate": approved / total_decisions if total_decisions else ZERO,
    }


def collect_signal_metrics(
    recommendations: tuple[Node, ...], *, rejection_count: int = 0
) -> dict[str, float]:
    """Collect recommendation quality metrics for one PM run."""
    return {
        "recommendation_count": float(len(recommendations)),
        "avg_confidence": _average(recommendations, "confidence"),
        "avg_technical_score": _average(recommendations, "technical_score"),
        "rejection_count": float(rejection_count),
    }


def collect_regime_attribution(
    scan_runs: tuple[Node, ...], market_snapshots: tuple[Node, ...]
) -> dict[str, float]:
    """Collect best-effort market context until Regime is linked into runs."""
    if not scan_runs and not market_snapshots:
        return {}
    return {
        "snapshots_used": float(len(market_snapshots)),
        "bar_count_total": sum(_number(node, "bar_count") for node in market_snapshots),
    }


def _average(nodes: tuple[Node, ...], prop: str) -> float:
    if not nodes:
        return ZERO
    return sum(_number(node, prop) for node in nodes) / len(nodes)


def _trigger_count(close_decisions: tuple[Node, ...], trigger: str) -> float:
    return float(sum(_is_trigger(decision, trigger) for decision in close_decisions))


def _is_trigger(decision: Node, trigger: str) -> bool:
    return decision.props.get("trigger") == trigger


def _number(node: Node | None, prop: str) -> float:
    if node is None:
        return ZERO
    try:
        return float(node.props.get(prop, ZERO))
    except (TypeError, ValueError):
        return ZERO
