"""Dispatcher run outcome helpers.

Agent: orchestration
Role: centralize run-stop reasons and small RunResult builders.
External I/O: none.
"""

from __future__ import annotations

from orchestration.trigger import RunResult, RunTrigger

REASON_SCAN_EMPTY = "scan produced no candidates"
REASON_ANALYSIS_EMPTY = "analysis produced no recommendations"
REASON_NO_ORDERS = "portfolio manager approved no orders"
REASON_NO_FILLS = "execution produced no submitted fills"
REASON_NO_MONITOR = "monitor produced no position decisions"
REASON_NO_REPORT = "reporter produced no snapshot"
REASON_NO_NARRATIVE = "reporter produced no trade narratives"


def active_trigger(trigger: RunTrigger, default_universe: str) -> RunTrigger:
    """Return a trigger with the dispatcher default universe filled in."""
    if trigger.universe:
        return trigger
    return trigger.model_copy(update={"universe": default_universe})


def stopped(run_id: str, steps_completed: int, reason: str) -> RunResult:
    """Build a graceful incomplete run result."""
    return RunResult(
        run_id=run_id,
        completed=False,
        snapshot=None,
        steps_completed=steps_completed,
        reason=reason,
    )
