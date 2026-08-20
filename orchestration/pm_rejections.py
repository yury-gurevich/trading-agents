"""Portfolio Manager rejection display helpers.

Agent: orchestration
Role: format rejected-order evidence consistently across read-only trace views.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contracts.portfolio_manager import RejectedOrder

_REASON_GATE = {
    "below_min_quantity": "min_order_quantity",
    "max_positions": "max_positions",
    "insufficient_cash": "cash_available",
    "invalid_stop_loss": "reward_risk",
    "reward_risk_below_min": "reward_risk",
    "sector_name_count": "max_names_per_sector",
    "sector_concentration": "max_sector_pct",
    "sector_not_evaluated": "max_sector_pct",
    "correlated_cluster_concentration": "correlated_cluster_pct",
    "correlation_not_evaluated": "correlated_cluster_pct",
}


def format_pm_rejection(rejection: RejectedOrder) -> str:
    """Return the compact PM rejection row used by trace renderers."""
    return (
        f"{rejection.ticker:<6} SKIP  {rejection.reason}"
        f"{_secondary_failure_suffix(rejection)}"
    )


def _secondary_failure_suffix(rejection: RejectedOrder) -> str:
    primary_gate = _REASON_GATE.get(rejection.reason)
    failed = tuple(
        outcome.name
        for outcome in rejection.gate_report
        if outcome.outcome != "passed" and outcome.name != primary_gate
    )
    if not failed:
        return ""
    return f" (also failed: {', '.join(failed)})"
