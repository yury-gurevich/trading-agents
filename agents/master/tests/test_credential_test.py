"""Credential-tested activation (DL-36 Piece A) — S104.

Agent: master
Role: verify test-before-handover — a required failure refuses activation + escalates;
      a pass hands over; costly passes are cached.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest

from agents.master.agent import MasterAgent
from agents.master.credential_test import (
    ActivationRefused,
    CredentialTest,
    PassCache,
    resolve_and_test,
)
from contracts.master import EHLOMessage
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from collections.abc import Mapping

    from agents.master.secret_map import SecretMap


class _Store:
    """Fake SecretStore backed by a dict."""

    def __init__(self, secrets: dict[str, str]) -> None:
        self._s = secrets

    def get_secret(self, name: str) -> str:
        return self._s.get(name, "")


_MAP: SecretMap = {"scanner": [("neo4j-uri", "NEO4J_URI")]}


def _passing(config: Mapping[str, str]) -> bool:
    return config.get("NEO4J_URI") == "good"


def _failing(_config: Mapping[str, str]) -> bool:
    return False


def test_resolve_and_test_hands_over_when_the_test_passes() -> None:
    store = _Store({"neo4j-uri": "good"})
    config, failures = resolve_and_test(
        "scanner", store, _MAP, (CredentialTest("neo4j", _passing),)
    )
    assert config == {"NEO4J_URI": "good"}
    assert failures == []


def test_resolve_and_test_names_a_failed_required_test() -> None:
    store = _Store({"neo4j-uri": "bad"})
    _, failures = resolve_and_test(
        "scanner", store, _MAP, (CredentialTest("neo4j", _failing),)
    )
    assert failures == ["neo4j"]


def test_resolve_and_test_optional_failure_is_non_blocking() -> None:
    store = _Store({"neo4j-uri": "x"})
    _, failures = resolve_and_test(
        "scanner", store, _MAP, (CredentialTest("opt", _failing, required=False),)
    )
    assert failures == []


def test_costly_test_uses_cached_pass_and_skips_the_rerun() -> None:
    calls: list[int] = []

    def run(_config: Mapping[str, str]) -> bool:
        calls.append(1)
        return True

    cache = PassCache(ttl_minutes=0)  # never expires
    store = _Store({"neo4j-uri": "x"})
    tests = (CredentialTest("llm", run, cost="costly"),)
    resolve_and_test("scanner", store, _MAP, tests, cache=cache)
    resolve_and_test("scanner", store, _MAP, tests, cache=cache)
    assert calls == [1]  # ran once; the second time was served from the cache


def test_pass_cache_ttl_expires() -> None:
    now = [datetime(2026, 7, 1, tzinfo=UTC)]
    cache = PassCache(ttl_minutes=5, clock=lambda: now[0])
    cache.record("x")
    assert cache.fresh("x")
    now[0] += timedelta(minutes=6)
    assert not cache.fresh("x")


def test_pass_cache_unknown_name_is_not_fresh() -> None:
    assert not PassCache().fresh("never-recorded")


def _master(
    tests: tuple[CredentialTest, ...], secrets: dict[str, str]
) -> tuple[InMemoryGraphStore, MasterAgent]:
    graph = InMemoryGraphStore()
    master = MasterAgent(
        graph=graph,
        grant_policy={"scanner": {"scan": {"level": "read"}}},
        secret_map=_MAP,
        secret_store=_Store(secrets),
        credential_tests=tests,
    )
    return graph, master


def _ehlo() -> EHLOMessage:
    return EHLOMessage(
        ephemeral_boot_id="boot1", agent_type="scanner", capability_declaration={}
    )


def test_activate_refuses_and_escalates_on_a_required_failure() -> None:
    graph, master = _master(
        (CredentialTest("neo4j", _failing),), {"neo4j-uri": "x"}
    )
    with pytest.raises(ActivationRefused):
        master.activate(_ehlo())
    (escalation,) = graph.list_nodes("Escalation")
    assert escalation.props["agent_type"] == "scanner"
    assert list(escalation.props["failed_credentials"]) == ["neo4j"]
    assert escalation.props["status"] == "open"
    assert graph.list_nodes("AgentInstance") == ()  # never activated


def test_activate_hands_over_config_when_the_test_passes() -> None:
    graph, master = _master(
        (CredentialTest("neo4j", _passing),), {"neo4j-uri": "good"}
    )
    activate = master.activate(_ehlo())
    assert activate.agent_type == "scanner"
    assert activate.config == {"NEO4J_URI": "good"}
    assert graph.list_nodes("Escalation") == ()
