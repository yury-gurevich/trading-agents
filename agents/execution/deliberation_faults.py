"""Execution deliberation fault records.

Agent: execution
Role: record loud evidence when the deliberation gate proceeds fail-open.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from kernel import AgentFault

if TYPE_CHECKING:
    from agents.execution.settings import ExecutionSettings
    from kernel import FaultSink


def record_unvetoed_submit(
    sink: FaultSink,
    pm_run_id: str,
    submitted: int,
    settings: ExecutionSettings,
) -> None:
    """Fault when a buy-carrying run submitted with no veto (DL-98).

    Fail-open is still the policy -- the run is never blocked -- but it must leave
    a record, so an absent veto can never again look like a clean run.
    """
    grace = settings.deliberation_grace_seconds
    sink.submit(
        AgentFault(
            source_agent="execution",
            source_module="agents.execution.deliberation_faults",
            capability="execute_pm_node",
            severity="error",
            error_type="DeliberationGraceExpired",
            message=(
                f"{pm_run_id}: submitted {submitted} order(s) carrying a buy with no "
                f"DeliberationRun after {grace}s"
            ),
            context={
                "pm_run_id": pm_run_id,
                "submitted": submitted,
                "grace_seconds": grace,
            },
        )
    )


def record_failed_open_submit(
    sink: FaultSink,
    pm_run_id: str,
    submitted: int,
    tickers: tuple[str, ...],
) -> None:
    """Fault when a linked veto contains fail-open reviews.

    The order still proceeds under the fail-open posture, but an unreviewed order
    must not look identical to a reviewed uphold.
    """
    sink.submit(
        AgentFault(
            source_agent="execution",
            source_module="agents.execution.deliberation_faults",
            capability="execute_pm_node",
            severity="error",
            error_type="DeliberationFailedOpenSubmit",
            message=(
                f"{pm_run_id}: submitted {submitted} order(s) after failed-open "
                f"deliberation for ticker(s): {', '.join(tickers)}"
            ),
            context={
                "pm_run_id": pm_run_id,
                "submitted": submitted,
                "failed_open_tickers": list(tickers),
            },
        )
    )
