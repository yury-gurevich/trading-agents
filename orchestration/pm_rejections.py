"""Portfolio Manager rejection display helpers.

Agent: orchestration
Role: format rejected-order evidence consistently across read-only trace views.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.portfolio_manager.domain.rejection_reasons import REASON_TO_GATE

if TYPE_CHECKING:
    from contracts.portfolio_manager import RejectedOrder


def format_pm_rejection(rejection: RejectedOrder) -> str:
    """Return the compact PM rejection row used by trace renderers."""
    return (
        f"{rejection.ticker:<6} SKIP  {rejection.reason}"
        f"{_secondary_failure_suffix(rejection)}"
    )


def _secondary_failure_suffix(rejection: RejectedOrder) -> str:
    primary_gate = REASON_TO_GATE.get(rejection.reason)
    failed = tuple(
        outcome.name
        for outcome in rejection.gate_report
        if outcome.outcome != "passed" and outcome.name != primary_gate
    )
    if not failed:
        return ""
    return f" (also failed: {', '.join(failed)})"
