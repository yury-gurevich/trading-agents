"""Credential probe activation evidence.

Agent: master
Role: render sanitized credential-test reports into graph props and faults.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from kernel.errors import AgentFault

if TYPE_CHECKING:
    from kernel import FaultSink


@dataclass(frozen=True)
class CredentialTransportFailure:
    """A sanitized non-blocking probe transport failure."""

    name: str
    reason: str


@dataclass(frozen=True)
class CredentialTestReport:
    """Resolved config plus credential-test evidence for one activation."""

    config: dict[str, object]
    applicable: tuple[str, ...]
    tested: tuple[str, ...]
    passed: tuple[str, ...]
    cached: tuple[str, ...]
    failed_required: tuple[str, ...]
    failed_optional: tuple[str, ...]
    transport_failures: tuple[CredentialTransportFailure, ...]


def credential_test_props(report: CredentialTestReport) -> dict[str, object]:
    """Return graph-safe activation props for credential-test evidence."""
    return {
        "credential_tests_declared": list(report.applicable),
        "credential_tests_tested": list(report.tested),
        "credential_tests_passed": list(report.passed),
        "credential_tests_cached": list(report.cached),
        "credential_tests_failed_optional": list(report.failed_optional),
        "credential_tests_transport_failed": [
            failure.name for failure in report.transport_failures
        ],
    }


def submit_transport_faults(
    sink: FaultSink, agent_type: str, report: CredentialTestReport
) -> None:
    """Emit one sanitized warning fault per credential-probe transport failure."""
    for failure in report.transport_failures:
        sink.submit(
            AgentFault(
                source_agent="master",
                source_module="agents.master.credential_test",
                capability="activate",
                severity="warning",
                error_type="CredentialProbeTransportFailure",
                message=(
                    f"credential probe transport failure for {agent_type}:"
                    f"{failure.name} ({failure.reason})"
                ),
                context={
                    "agent_type": agent_type,
                    "credential_test": failure.name,
                    "reason": failure.reason,
                },
            )
        )
