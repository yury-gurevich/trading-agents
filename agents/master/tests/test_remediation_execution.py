"""Automatic remediation execution tests.

Agent: master
Role: verify safe executor execution, one-shot gating, and attempt graph writes.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.master.key_vault import CachingSecretStore
from agents.master.remediation import RemediationPlan
from agents.master.remediation_execution import (
    RefetchFromKeyVaultExecutor,
    run_remediation,
)
from agents.master.remediation_records import RemediationAttempt

if TYPE_CHECKING:
    from collections.abc import Mapping

_SAFE = RemediationPlan("refetch-from-key-vault", "Fetch again.", True, "planned")
_MANUAL = RemediationPlan("rotate-credential", "Rotate.", False, "planned")


class _Executor:
    name = "refetch-from-key-vault"

    def __init__(self, result: RemediationAttempt | Exception) -> None:
        self.result = result
        self.calls = 0

    def run(self, context: Mapping[str, object]) -> RemediationAttempt:
        assert context["agent_type"] == "scanner"
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class _Store:
    def __init__(self, values: dict[str, str]) -> None:
        self.values = values
        self.calls = 0

    def get_secret(self, name: str) -> str:
        self.calls += 1
        return self.values[name]


def _context() -> dict[str, object]:
    return {"agent_type": "scanner", "failed_credentials": ("neo4j",)}


def test_run_remediation_skips_non_auto_eligible_plan() -> None:
    attempt = run_remediation(
        _context(),
        _MANUAL,
        {},
        prior_auto_attempts=0,
        max_auto_remediation_attempts=1,
    )
    assert attempt.status == "skipped"
    assert attempt.auto is False


def test_run_remediation_skips_when_attempt_cap_is_reached() -> None:
    attempt = run_remediation(
        _context(),
        _SAFE,
        {"refetch-from-key-vault": _Executor(RemediationAttempt("", "", "", "", True))},
        prior_auto_attempts=1,
        max_auto_remediation_attempts=1,
    )
    assert attempt.message == "auto-remediation attempt cap reached"


def test_run_remediation_skips_when_executor_is_missing() -> None:
    attempt = run_remediation(
        _context(),
        _SAFE,
        {},
        prior_auto_attempts=0,
        max_auto_remediation_attempts=1,
    )
    assert attempt.message == "no executor registered"


def test_run_remediation_records_executor_success() -> None:
    expected = RemediationAttempt(_SAFE.remediation, "succeeded", "ok", "x", True)
    executor = _Executor(expected)
    attempt = run_remediation(
        _context(),
        _SAFE,
        {"refetch-from-key-vault": executor},
        prior_auto_attempts=0,
        max_auto_remediation_attempts=1,
    )
    assert attempt == expected
    assert executor.calls == 1


def test_run_remediation_records_executor_exception() -> None:
    attempt = run_remediation(
        _context(),
        _SAFE,
        {"refetch-from-key-vault": _Executor(RuntimeError("boom"))},
        prior_auto_attempts=0,
        max_auto_remediation_attempts=1,
    )
    assert attempt.status == "failed"
    assert attempt.auto is True
    assert "RuntimeError" in attempt.message


def test_refetch_executor_invalidates_secret_cache() -> None:
    inner = _Store({"neo4j-uri": "bad"})
    cache = CachingSecretStore(inner, ttl_minutes=0)
    assert cache.get_secret("neo4j-uri") == "bad"
    inner.values["neo4j-uri"] = "good"
    attempt = RefetchFromKeyVaultExecutor(cache).run({})
    assert attempt.status == "succeeded"
    assert cache.get_secret("neo4j-uri") == "good"
    assert inner.calls == 2


def test_refetch_executor_succeeds_without_cache_layer() -> None:
    attempt = RefetchFromKeyVaultExecutor(object()).run({})
    assert attempt.status == "succeeded"
    assert attempt.message == (
        "no cache layer present; retry will use the configured store"
    )
