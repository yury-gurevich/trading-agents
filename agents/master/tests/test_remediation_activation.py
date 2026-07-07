"""Remediation plan persistence and activation wiring tests.

Agent: master
Role: verify Escalation -> RemediationPlan graph writes and opt-in planner wiring
      on credential-test refusal.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from agents.master.agent import MasterAgent
from agents.master.credential_test import ActivationRefused, CredentialTest
from agents.master.remediation import (
    FALLBACK_REMEDIATION,
    Remediation,
    RemediationPlan,
)
from agents.master.settings import MasterSettings
from agents.master.store import write_escalation, write_remediation_plan
from contracts.master import EHLOMessage
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from collections.abc import Mapping

_CATALOGUE = (
    Remediation("refetch-from-key-vault", "Fetch the value again.", False),
    Remediation(FALLBACK_REMEDIATION, "Escalate to a human.", False),
)
_MAP = {"scanner": [("postgres-dsn", "POSTGRES_DSN")]}


class _LLM:
    """Fake planner LLM."""

    def __init__(self) -> None:
        self.system_prompts: list[str] = []

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        self.system_prompts.append(system)
        del user, tool_schema
        return (
            '{"remediation": "refetch-from-key-vault", '
            '"rationale": "Credential can be fetched again."}'
        )


class _Store:
    """Fake SecretStore backed by a dict."""

    def __init__(self, values: dict[str, str]) -> None:
        self._values = values

    def get_secret(self, name: str) -> str:
        return self._values.get(name, "")


def _ehlo() -> EHLOMessage:
    return EHLOMessage(
        ephemeral_boot_id="boot1", agent_type="scanner", capability_declaration={}
    )


def _failing(_config: Mapping[str, str]) -> bool:
    return False


def test_write_remediation_plan_links_it_to_escalation() -> None:
    graph = InMemoryGraphStore()
    escalation = write_escalation(graph, "scanner", ("postgres",), "automatic")
    plan = RemediationPlan("refetch-from-key-vault", "Fetch again.", True, "planned")
    node = write_remediation_plan(graph, escalation.key, plan)
    assert node.props["remediation"] == "refetch-from-key-vault"
    assert node.props["auto_eligible"] is True
    linked = tuple(
        graph.descendants(escalation, max_depth=1, edge_types={"PLANNED_BY"})
    )
    assert linked == (node,)


def test_write_remediation_plan_requires_existing_escalation() -> None:
    graph = InMemoryGraphStore()
    plan = RemediationPlan(FALLBACK_REMEDIATION, "Escalate.", False, "planned")
    with pytest.raises(KeyError, match="no Escalation"):
        write_remediation_plan(graph, "missing", plan)


def test_activate_records_plan_before_refusing_activation() -> None:
    graph = InMemoryGraphStore()
    llm = _LLM()
    master = MasterAgent(
        graph=graph,
        settings=MasterSettings(
            remediation_mode="automatic",
            auto_remediation_scope="safe_only",
        ),
        grant_policy={"scanner": {"scan": {"level": "read"}}},
        secret_map=_MAP,
        secret_store=_Store({"postgres-dsn": "bad"}),
        credential_tests=(CredentialTest("postgres", _failing),),
        remediation_llm=llm,
        remediation_catalogue=_CATALOGUE,
        remediation_system_prompt="compiled selector prompt",
    )
    with pytest.raises(ActivationRefused):
        master.activate(_ehlo())
    (escalation,) = graph.list_nodes("Escalation")
    (plan,) = graph.list_nodes("RemediationPlan")
    assert plan.props["remediation"] == "refetch-from-key-vault"
    assert plan.props["auto_eligible"] is True
    linked = tuple(
        graph.descendants(escalation, max_depth=1, edge_types={"PLANNED_BY"})
    )
    assert linked == (plan,)
    assert llm.system_prompts == ["compiled selector prompt"]
