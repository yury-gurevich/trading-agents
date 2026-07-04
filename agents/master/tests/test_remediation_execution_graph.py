"""Remediation execution graph tests.

Agent: master
Role: verify remediation attempts are written and capped across escalations.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from agents.master.remediation import Remediation, RemediationPlan
from agents.master.remediation_execution import plan_and_run_remediation
from agents.master.remediation_records import RemediationAttempt
from agents.master.store import (
    write_escalation,
    write_escalation_remediation_outcome,
    write_remediation_attempt,
)
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from collections.abc import Mapping

_SAFE = RemediationPlan("refetch-from-key-vault", "Fetch again.", True, "planned")


class _Executor:
    name = "refetch-from-key-vault"

    def __init__(self, result: RemediationAttempt | Exception) -> None:
        self.result = result

    def run(self, _context: Mapping[str, object]) -> RemediationAttempt:
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class _LLM:
    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del system, user, tool_schema
        return '{"remediation": "refetch-from-key-vault", "rationale": "safe"}'


def test_write_remediation_attempt_links_to_escalation() -> None:
    graph = InMemoryGraphStore()
    escalation = write_escalation(graph, "scanner", ("neo4j",), "automatic")
    attempt = RemediationAttempt(_SAFE.remediation, "succeeded", "ok", "refetch", True)
    node = write_remediation_attempt(graph, escalation.key, attempt)
    assert node.props["agent_type"] == "scanner"
    linked = tuple(
        graph.descendants(escalation, max_depth=1, edge_types={"ATTEMPTED_BY"})
    )
    assert linked == (node,)


def test_write_remediation_attempt_requires_existing_escalation() -> None:
    with pytest.raises(KeyError, match="no Escalation"):
        write_remediation_attempt(
            InMemoryGraphStore(),
            "missing",
            RemediationAttempt(_SAFE.remediation, "skipped", "nope", "none", False),
        )


def test_write_escalation_remediation_outcome_requires_existing_escalation() -> None:
    with pytest.raises(KeyError, match="no Escalation"):
        write_escalation_remediation_outcome(
            InMemoryGraphStore(),
            "missing",
            RemediationAttempt(_SAFE.remediation, "skipped", "nope", "none", False),
            resolved=False,
        )


def test_plan_and_run_remediation_writes_plan_and_attempt() -> None:
    graph = InMemoryGraphStore()
    escalation = write_escalation(graph, "scanner", ("neo4j",), "automatic")
    attempt = plan_and_run_remediation(
        graph=graph,
        escalation=escalation,
        llm=_LLM(),
        catalogue=(Remediation(_SAFE.remediation, "Fetch again.", False),),
        system_prompt="compiled",
        scope="safe_only",
        mode="automatic",
        executors={
            "refetch-from-key-vault": _Executor(
                RemediationAttempt(_SAFE.remediation, "succeeded", "ok", "x", True)
            )
        },
        max_auto_remediation_attempts=1,
    )
    assert attempt is not None
    assert attempt.status == "succeeded"
    assert len(graph.list_nodes("RemediationPlan")) == 1
    assert len(graph.list_nodes("RemediationAttempt")) == 1


def test_plan_and_run_remediation_skips_when_selector_is_unavailable() -> None:
    graph = InMemoryGraphStore()
    escalation = write_escalation(graph, "scanner", ("neo4j",), "automatic")
    attempt = plan_and_run_remediation(
        graph=graph,
        escalation=escalation,
        llm=None,
        catalogue=(Remediation(_SAFE.remediation, "Fetch again.", False),),
        system_prompt="compiled",
        scope="safe_only",
        mode="automatic",
        executors={},
        max_auto_remediation_attempts=1,
    )
    assert attempt is None
    assert not graph.list_nodes("RemediationPlan")
    assert not graph.list_nodes("RemediationAttempt")


def test_plan_and_run_remediation_respects_prior_attempt_cap() -> None:
    graph = InMemoryGraphStore()
    old = write_escalation(graph, "scanner", ("neo4j",), "automatic")
    write_remediation_attempt(
        graph,
        old.key,
        RemediationAttempt(_SAFE.remediation, "failed", "old", "x", True),
    )
    new = write_escalation(graph, "scanner", ("neo4j",), "automatic")
    attempt = plan_and_run_remediation(
        graph=graph,
        escalation=new,
        llm=_LLM(),
        catalogue=(Remediation(_SAFE.remediation, "Fetch again.", False),),
        system_prompt="compiled",
        scope="safe_only",
        mode="automatic",
        executors={"refetch-from-key-vault": _Executor(RuntimeError("unused"))},
        max_auto_remediation_attempts=1,
    )
    assert attempt is not None
    assert attempt.status == "skipped"
    assert attempt.message == "auto-remediation attempt cap reached"
