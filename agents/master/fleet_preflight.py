"""Test and record whether every declared fleet credential is ready.

Agent: master
Role: run the master-owned fleet readiness check and its bounded schedule.
External I/O: graph database and injected secret-store credential probes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from agents.master.credential_test import resolve_and_test_report
from kernel.errors import AgentFault

if TYPE_CHECKING:
    from agents.master.credential_report import CredentialTestReport
    from agents.master.credential_test import CredentialTest, PassCache
    from agents.master.grants import GrantPolicy
    from agents.master.key_vault import SecretStore
    from agents.master.secret_map import SecretMap
    from kernel import FaultSink, GraphStore


@dataclass(frozen=True)
class PreflightFailure:
    """One sanitized failed credential check for an agent type."""

    probe: str
    agent_type: str
    klass: str
    reason: str


@dataclass(frozen=True)
class FleetPreflightResult:
    """The durable fleet readiness outcome for one scheduled check."""

    passed: bool
    failures: tuple[PreflightFailure, ...]


def run_fleet_preflight(
    *,
    graph: GraphStore,
    sink: FaultSink,
    secret_store: SecretStore,
    secret_map: SecretMap,
    grant_policy: GrantPolicy,
    credential_tests: tuple[CredentialTest, ...],
    pass_cache: PassCache | None,
    now: datetime,
) -> FleetPreflightResult:
    """Test every grant-policy agent type and record fleet readiness."""
    failures: list[PreflightFailure] = []
    agent_types_checked = tuple(sorted(grant_policy))
    for agent_type in agent_types_checked:
        try:
            report = resolve_and_test_report(
                agent_type,
                secret_store,
                secret_map,
                credential_tests,
                cache=pass_cache,
            )
        except Exception as exc:
            failures.append(
                PreflightFailure("secrets", agent_type, "transient", type(exc).__name__)
            )
            continue
        failures.extend(_report_failures(agent_type, report))
    checked_at = now.astimezone(UTC).isoformat(timespec="seconds")
    failure_values = [
        f"{failure.klass}:{failure.agent_type}:{failure.probe}:{failure.reason}"
        for failure in failures
    ]
    graph.merge_node(
        "FleetPreflight",
        f"preflight:{checked_at}",
        {
            "checked_at": checked_at,
            "passed": not failures,
            "failure_count": len(failures),
            "failures": failure_values,
            "agent_types_checked": list(agent_types_checked),
        },
    )
    if failures:
        classes = sorted({failure.klass for failure in failures})
        sink.submit(
            AgentFault(
                source_agent="master",
                source_module="agents.master.fleet_preflight",
                capability="fleet_preflight",
                severity="critical",
                error_type="FleetPreflightFailure",
                message=(
                    f"fleet preflight failure_count={len(failures)} "
                    f"classes={','.join(classes)}"
                ),
                context={"failures": failure_values},
            )
        )
    return FleetPreflightResult(not failures, tuple(failures))


def _report_failures(
    agent_type: str, report: CredentialTestReport
) -> list[PreflightFailure]:
    """Convert one agent's sanitized report to de-duplicated readiness failures."""
    failures: list[PreflightFailure] = []
    seen: set[str] = set()
    for credential_failure in report.credential_failures:
        if credential_failure.name not in seen:
            klass = (
                "unrecoverable"
                if credential_failure.reason.startswith("unrecoverable:")
                else "unexpected"
            )
            failures.append(
                PreflightFailure(
                    credential_failure.name,
                    agent_type,
                    klass,
                    credential_failure.reason,
                )
            )
            seen.add(credential_failure.name)
    for transport_failure in report.transport_failures:
        if transport_failure.name not in seen:
            failures.append(
                PreflightFailure(
                    transport_failure.name,
                    agent_type,
                    "transient",
                    transport_failure.reason,
                )
            )
            seen.add(transport_failure.name)
    return failures
