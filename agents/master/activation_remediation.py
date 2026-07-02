"""Activation-time remediation orchestration.

Agent: master
Role: plan, execute, re-test, and record bounded remediation during activation.
External I/O: graph writes via injected GraphStore; secret reads via injected store.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.master.credential_test import ActivationRefused, resolve_and_test
from agents.master.remediation_execution import (
    RemediationAttempt,
    plan_and_try_remediation,
)
from agents.master.store import (
    write_escalation_remediation_outcome,
    write_remediation_attempt,
)
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from collections.abc import Mapping

    from agents.master.credential_test import CredentialTest, PassCache
    from agents.master.key_vault import SecretStore
    from agents.master.remediation import Remediation
    from agents.master.remediation_execution import RemediationExecutor, RemediationRun
    from agents.master.secret_map import SecretMap
    from agents.master.settings import MasterSettings
    from kernel import FaultSink, GraphStore, LLMClient
    from kernel.graph import Node


def handle_activation_remediation(
    *,
    graph: GraphStore,
    sink: FaultSink,
    settings: MasterSettings,
    escalation: Node,
    agent_type: str,
    secret_store: SecretStore,
    secret_map: SecretMap,
    credential_tests: tuple[CredentialTest, ...],
    pass_cache: PassCache | None,
    llm: LLMClient | None,
    catalogue: tuple[Remediation, ...],
    system_prompt: str,
    executors: Mapping[str, RemediationExecutor],
) -> None:
    """Run the bounded activation remediation flow and record the final attempt."""
    run: RemediationRun | None = None
    with fault_boundary(
        sink,
        agent="master",
        module="agents.master.activation_remediation",
        capability="run_remediation",
        reraise=False,
    ):
        run = plan_and_try_remediation(
            graph=graph,
            escalation=escalation,
            llm=llm,
            catalogue=catalogue,
            system_prompt=system_prompt,
            scope=settings.auto_remediation_scope,
            mode=settings.remediation_mode,
            executors=executors,
            max_auto_remediation_attempts=settings.max_auto_remediation_attempts,
        )
    if run is None:
        return
    attempt = _finalize_attempt(
        agent_type, secret_store, secret_map, credential_tests, pass_cache, run.attempt
    )
    write_remediation_attempt(graph, escalation.key, attempt)
    write_escalation_remediation_outcome(
        graph,
        escalation.key,
        attempt,
        resolved=attempt.status == "succeeded",
    )
    if attempt.status == "succeeded":
        raise ActivationRefused("credential remediation succeeded; re-EHLO required")


def _finalize_attempt(
    agent_type: str,
    secret_store: SecretStore,
    secret_map: SecretMap,
    credential_tests: tuple[CredentialTest, ...],
    pass_cache: PassCache | None,
    attempt: RemediationAttempt,
) -> RemediationAttempt:
    if attempt.status != "succeeded":
        return attempt
    _, failures = resolve_and_test(
        agent_type,
        secret_store,
        secret_map,
        credential_tests,
        cache=pass_cache,
    )
    if not failures:
        return attempt
    return RemediationAttempt(
        attempt.remediation,
        "failed",
        f"post-remediation credential test failed: {', '.join(failures)}",
        attempt.executor,
        attempt.auto,
    )
