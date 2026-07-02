"""Auto-remediation activation tests.

Agent: master
Role: prove safe remediation retries credential tests once, then forces human review.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from agents.master.agent import MasterAgent
from agents.master.credential_test import ActivationRefused, CredentialTest
from agents.master.key_vault import CachingSecretStore
from agents.master.remediation import Remediation
from agents.master.remediation_execution import RefetchFromKeyVaultExecutor
from agents.master.settings import MasterSettings
from contracts.master import EHLOMessage
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from collections.abc import Mapping

_MAP = {"scanner": [("neo4j-uri", "NEO4J_URI")]}
_CATALOGUE = (Remediation("refetch-from-key-vault", "Fetch again.", False),)
_TEST_NAME = "blank-key-vault-secret"


class _LLM:
    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del system, user, tool_schema
        return '{"remediation": "refetch-from-key-vault", "rationale": "safe"}'


class _RotatingStore:
    def __init__(self, values: tuple[str, ...]) -> None:
        self._values = values
        self.calls = 0

    def get_secret(self, _name: str) -> str:
        value = self._values[min(self.calls, len(self._values) - 1)]
        self.calls += 1
        return value


def _passing(config: Mapping[str, str]) -> bool:
    return config.get("NEO4J_URI") == "good"


def _ehlo() -> EHLOMessage:
    return EHLOMessage(
        ephemeral_boot_id="boot1", agent_type="scanner", capability_declaration={}
    )


def _master(
    graph: InMemoryGraphStore,
    secret_store: CachingSecretStore,
) -> MasterAgent:
    executor = RefetchFromKeyVaultExecutor(secret_store)
    return MasterAgent(
        graph=graph,
        settings=MasterSettings(
            remediation_mode="automatic",
            auto_remediation_scope="safe_only",
            max_auto_remediation_attempts=1,
        ),
        grant_policy={"scanner": {"scan": {"level": "read"}}},
        secret_map=_MAP,
        secret_store=secret_store,
        credential_tests=(CredentialTest(_TEST_NAME, _passing),),
        remediation_llm=_LLM(),
        remediation_catalogue=_CATALOGUE,
        remediation_executors={executor.name: executor},
    )


def test_safe_refetch_remediation_retries_and_activates() -> None:
    graph = InMemoryGraphStore()
    inner = _RotatingStore(("bad", "good"))
    cache = CachingSecretStore(inner, ttl_minutes=0)
    master = _master(graph, cache)
    with pytest.raises(ActivationRefused, match="re-EHLO"):
        master.activate(_ehlo())
    assert not graph.list_nodes("AgentInstance")
    activate = master.activate(_ehlo())
    assert activate.config == {"NEO4J_URI": "good"}
    assert inner.calls == 2
    (attempt,) = graph.list_nodes("RemediationAttempt")
    assert attempt.props["status"] == "succeeded"
    (escalation,) = graph.list_nodes("Escalation")
    assert escalation.props["resolution_status"] == "resolved"
    assert escalation.props["auto_attempts_used"] == 1
    assert graph.list_nodes("AgentInstance")


def test_auto_remediation_is_one_shot_before_human_review() -> None:
    graph = InMemoryGraphStore()
    inner = _RotatingStore(("bad",))
    cache = CachingSecretStore(inner, ttl_minutes=0)
    master = _master(graph, cache)
    with pytest.raises(ActivationRefused):
        master.activate(_ehlo())
    with pytest.raises(ActivationRefused):
        master.activate(_ehlo())
    attempts = graph.list_nodes("RemediationAttempt")
    assert [node.props["status"] for node in attempts] == ["failed", "skipped"]
    assert [node.props["auto"] for node in attempts] == [True, False]
    escalations = graph.list_nodes("Escalation")
    assert [node.props["resolution_status"] for node in escalations] == ["open", "open"]
    assert [node.props["mode_after_remediation"] for node in escalations] == [
        "manual",
        "manual",
    ]
    assert inner.calls == 2
