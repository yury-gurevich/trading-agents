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
    from kernel.errors import Severity


def record_unvetoed_submit(
    sink: FaultSink,
    pm_run_id: str,
    submitted: int,
    settings: ExecutionSettings,
    *,
    blocked_count: int = 0,
) -> None:
    """Fault when a buy-carrying run submitted with no veto (DL-98).

    Fail-open is still the policy -- the run is never blocked -- but it must leave
    a record, so an absent veto can never again look like a clean run.
    """
    grace = settings.deliberation_grace_seconds
    posture = settings.deliberation_posture
    sink.submit(
        AgentFault(
            source_agent="execution",
            source_module="agents.execution.deliberation_faults",
            capability="execute_pm_node",
            severity=_severity(posture),
            error_type="DeliberationGraceExpired",
            message=(
                f"{pm_run_id}: posture={posture} submitted {submitted} order(s) "
                f"and blocked {blocked_count} buy order(s) with no DeliberationRun "
                f"after {grace}s"
            ),
            context={
                "pm_run_id": pm_run_id,
                "submitted": submitted,
                "blocked_count": blocked_count,
                "grace_seconds": grace,
                "deliberation_posture": posture,
            },
        )
    )


def record_failed_open_submit(
    sink: FaultSink,
    pm_run_id: str,
    submitted: int,
    tickers: tuple[str, ...],
    settings: ExecutionSettings,
) -> None:
    """Fault when a linked veto contains fail-open reviews.

    The order still proceeds under the fail-open posture, but an unreviewed order
    must not look identical to a reviewed uphold.
    """
    posture = settings.deliberation_posture
    sink.submit(
        AgentFault(
            source_agent="execution",
            source_module="agents.execution.deliberation_faults",
            capability="execute_pm_node",
            severity=_severity(posture),
            error_type="DeliberationFailedOpenSubmit",
            message=(
                f"{pm_run_id}: posture={posture} submitted {submitted} order(s) "
                f"after failed-open deliberation for ticker(s): {', '.join(tickers)}"
            ),
            context={
                "pm_run_id": pm_run_id,
                "submitted": submitted,
                "failed_open_tickers": list(tickers),
                "deliberation_posture": posture,
            },
        )
    )


def _severity(posture: str) -> Severity:
    """Advisory fail-open is expected; binding fail-open is an error."""
    return "warning" if posture == "advisory" else "error"
