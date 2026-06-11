"""Stage-gate metric parsing helpers.

Agent: execution
Role: parse reporter Snapshot metrics for stage promotion evidence.
External I/O: none.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel import Node


def avg_approval_rate(snapshots: tuple[Node, ...]) -> float:
    """Return average portfolio approval rate across Snapshot nodes."""
    rates = tuple(_approval_rate(snapshot) for snapshot in snapshots)
    return sum(rates) / len(rates) if rates else 0.0


def _approval_rate(snapshot: Node) -> float:
    metrics = snapshot.props.get("metrics", {})
    if not isinstance(metrics, Mapping):
        return 0.0
    portfolio = metrics.get("portfolio", {})
    if not isinstance(portfolio, Mapping):
        return 0.0
    try:
        return float(portfolio.get("approval_rate", 0.0))
    except (TypeError, ValueError):
        return 0.0
