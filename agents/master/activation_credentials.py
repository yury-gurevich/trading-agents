"""Credential-gated activation helpers.

Agent: master
Role: refuse activation and invoke manual remediation when required probes fail.
External I/O: graph database via injected GraphStore.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.master.activation_remediation import handle_activation_remediation
from agents.master.credential_test import ActivationRefused
from agents.master.store import write_escalation

if TYPE_CHECKING:
    from collections.abc import Mapping

    from agents.master.credential_report import CredentialTestReport
    from agents.master.credential_test import CredentialTest, PassCache
    from agents.master.key_vault import SecretStore
    from agents.master.remediation import Remediation
    from agents.master.remediation_execution import RemediationExecutor
    from agents.master.secret_map import SecretMap
    from agents.master.settings import MasterSettings
    from kernel import FaultSink, GraphStore, LLMClient


def refuse_activation_for_failed_credentials(
    *,
    graph: GraphStore,
    sink: FaultSink,
    settings: MasterSettings,
    report: CredentialTestReport,
    agent_type: str,
    secret_store: SecretStore,
    secret_map: SecretMap,
    credential_tests: tuple[CredentialTest, ...],
    pass_cache: PassCache | None,
    remediation_llm: LLMClient | None,
    remediation_catalogue: tuple[Remediation, ...],
    remediation_system_prompt: str,
    remediation_executors: Mapping[str, RemediationExecutor],
) -> None:
    """Raise ActivationRefused after recording escalation/remediation evidence."""
    failures = tuple(report.failed_required)
    if not failures:
        return
    escalation = write_escalation(
        graph,
        agent_type,
        failures,
        settings.remediation_mode,
    )
    handle_activation_remediation(
        graph=graph,
        sink=sink,
        settings=settings,
        escalation=escalation,
        agent_type=agent_type,
        secret_store=secret_store,
        secret_map=secret_map,
        credential_tests=credential_tests,
        pass_cache=pass_cache,
        llm=remediation_llm,
        catalogue=remediation_catalogue,
        system_prompt=remediation_system_prompt,
        executors=remediation_executors,
    )
    raise ActivationRefused(
        f"credential test(s) failed for {agent_type!r}: {list(failures)}"
    )
