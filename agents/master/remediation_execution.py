"""Automatic remediation execution for master activation failures.

Agent: master
Role: run one bounded, injected remediation executor and build auditable attempts.
External I/O: delegated only to injected executors.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from agents.master.remediation import RemediationPlan, plan_remediation
from agents.master.store import write_remediation_attempt, write_remediation_plan

if TYPE_CHECKING:
    from collections.abc import Mapping

    from agents.master.remediation import Remediation
    from kernel import GraphStore, LLMClient
    from kernel.graph import Node


@dataclass(frozen=True)
class RemediationAttempt:
    """One execution attempt for a planned remediation."""

    remediation: str
    status: str
    message: str
    executor: str
    auto: bool


@dataclass(frozen=True)
class RemediationRun:
    """A planned remediation plus the executor's immediate result."""

    plan: RemediationPlan
    attempt: RemediationAttempt


class RemediationExecutor(Protocol):
    """Injected executor for one non-destructive remediation."""

    name: str

    def run(self, context: Mapping[str, object]) -> RemediationAttempt:
        """Execute against the failure context and return an auditable result."""
        ...  # pragma: no cover - protocol declaration only.


@runtime_checkable
class _CacheInvalidator(Protocol):
    def invalidate(self) -> None:
        """Clear cached secret values."""
        ...  # pragma: no cover - protocol declaration only.


class RefetchFromKeyVaultExecutor:
    """Safe executor: clear the secret cache so the retry re-fetches from the store."""

    name = "refetch-from-key-vault"

    def __init__(self, secret_store: object) -> None:
        """Create an executor over the master's configured secret store."""
        self._secret_store = secret_store

    def run(self, context: Mapping[str, object]) -> RemediationAttempt:
        """Invalidate the cache if present so the retry re-fetches credentials."""
        del context
        if isinstance(self._secret_store, _CacheInvalidator):
            self._secret_store.invalidate()
            message = "secret cache invalidated; retry will re-fetch secrets"
        else:
            message = "no cache layer present; retry will use the configured store"
        return RemediationAttempt(self.name, "succeeded", message, self.name, True)


def run_remediation(
    escalation: Mapping[str, object],
    plan: RemediationPlan,
    executors: Mapping[str, RemediationExecutor],
    *,
    prior_auto_attempts: int,
    max_auto_remediation_attempts: int,
) -> RemediationAttempt:
    """Run one eligible executor, or return an auditable skipped/failed attempt."""
    if not plan.auto_eligible:
        return _skipped(plan.remediation, "plan is not auto-eligible")
    if prior_auto_attempts >= max_auto_remediation_attempts:
        return _skipped(plan.remediation, "auto-remediation attempt cap reached")
    executor = executors.get(plan.remediation)
    if executor is None:
        return _skipped(plan.remediation, "no executor registered")
    try:
        return executor.run(escalation)
    except Exception as exc:
        return RemediationAttempt(
            plan.remediation,
            "failed",
            f"executor raised {type(exc).__name__}",
            executor.name,
            True,
        )


def plan_and_run_remediation(
    *,
    graph: GraphStore,
    escalation: Node,
    llm: LLMClient | None,
    catalogue: tuple[Remediation, ...],
    system_prompt: str,
    scope: str,
    mode: str,
    executors: Mapping[str, RemediationExecutor],
    max_auto_remediation_attempts: int,
) -> RemediationAttempt | None:
    """Write a plan, run at most one auto remediation, then write its attempt."""
    run = plan_and_try_remediation(
        graph=graph,
        escalation=escalation,
        llm=llm,
        catalogue=catalogue,
        system_prompt=system_prompt,
        scope=scope,
        mode=mode,
        executors=executors,
        max_auto_remediation_attempts=max_auto_remediation_attempts,
    )
    if run is None:
        return None
    write_remediation_attempt(graph, escalation.key, run.attempt)
    return run.attempt


def plan_and_try_remediation(
    *,
    graph: GraphStore,
    escalation: Node,
    llm: LLMClient | None,
    catalogue: tuple[Remediation, ...],
    system_prompt: str,
    scope: str,
    mode: str,
    executors: Mapping[str, RemediationExecutor],
    max_auto_remediation_attempts: int,
) -> RemediationRun | None:
    """Write a plan and run an executor, but leave final attempt logging to caller."""
    if llm is None or not catalogue:
        return None
    context = {**dict(escalation.props), "key": escalation.key}
    plan = plan_remediation(
        context,
        catalogue,
        llm,
        scope=scope,
        mode=mode,
        system_prompt=system_prompt,
    )
    write_remediation_plan(graph, escalation.key, plan)
    attempt = run_remediation(
        context,
        plan,
        executors,
        prior_auto_attempts=_prior_auto_attempts(graph, context, plan.remediation),
        max_auto_remediation_attempts=max_auto_remediation_attempts,
    )
    return RemediationRun(plan, attempt)


def _prior_auto_attempts(
    graph: GraphStore, context: Mapping[str, object], remediation: str
) -> int:
    agent_type = str(context.get("agent_type", ""))
    raw_failed = context.get("failed_credentials", ())
    failed = tuple(raw_failed) if isinstance(raw_failed, list | tuple) else ()
    return sum(
        1
        for node in graph.list_nodes("RemediationAttempt")
        if node.props.get("auto") is True
        and node.props.get("agent_type") == agent_type
        and tuple(node.props.get("failed_credentials", ())) == failed
        and node.props.get("remediation") == remediation
    )


def _skipped(remediation: str, message: str) -> RemediationAttempt:
    return RemediationAttempt(remediation, "skipped", message, "none", False)
