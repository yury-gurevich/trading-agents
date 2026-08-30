"""Test credentials before handover (DL-36 Piece A).

Agent: master
Role: test each credential the master would distribute (via resolve_config) before it
      is handed to an agent; a required-credential failure blocks activation (fail-safe,
      like the frenzy guard). Tests are INJECTED — the master substrate imports no
      agent or probe code (agent independence / ADR-0012); a pack supplies the actual
      test functions. Costly tests reuse a cached pass so a live call is not made on
      every activation (cheap live + cache costly, DL-36).
External I/O: none directly (delegates to injected test callables + the SecretStore).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Literal

from agents.master.credential_report import (
    CredentialTestReport,
    CredentialTransportFailure,
)
from agents.master.credential_result import CheckResult, coerce_result
from agents.master.secret_map import resolve_config

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from agents.master.key_vault import SecretStore
    from agents.master.secret_map import SecretMap

Cost = Literal["cheap", "costly"]


class ActivationRefused(ValueError):  # noqa: N818 - a state ("refused"), not an *Error
    """A required credential failed its test — the agent must not be activated.

    Subclasses ValueError so the master HTTP server maps it to a 422 (the agent stays
    PRE_FLIGHT); the master records an Escalation before raising it.
    """


@dataclass(frozen=True)
class CredentialTest:
    """One credential check run against the resolved config.

    ``run(config)`` returns True or ``CredentialCheckResult(status="passed")`` when
    the credential works. A ``required`` credential failure blocks activation; a
    transport failure is faulted by the caller but does not block.
    """

    name: str
    run: Callable[[Mapping[str, str]], CheckResult]
    required: bool = True
    cost: Cost = "cheap"
    agent_types: tuple[str, ...] = ()


class PassCache:
    """Remembers costly passes so a live call is skipped within the TTL (0 = never)."""

    def __init__(
        self, ttl_minutes: int = 0, *, clock: Callable[[], datetime] | None = None
    ) -> None:
        """TTL cache in minutes (0 = never expires) with an injectable clock."""
        self._ttl = timedelta(minutes=ttl_minutes)
        self._never = ttl_minutes == 0
        self._clock = clock or (lambda: datetime.now(UTC))
        self._passes: dict[str, datetime] = {}

    def fresh(self, name: str) -> bool:
        """Return True if *name* passed recently enough to skip a live re-test."""
        at = self._passes.get(name)
        if at is None:
            return False
        return self._never or (self._clock() - at) < self._ttl

    def record(self, name: str) -> None:
        """Remember that *name* passed now."""
        self._passes[name] = self._clock()


def resolve_and_test(
    agent_type: str,
    store: SecretStore,
    secret_map: SecretMap,
    tests: tuple[CredentialTest, ...],
    *,
    cache: PassCache | None = None,
) -> tuple[dict[str, object], list[str]]:
    """Resolve secrets and return the backward-compatible failure-name tuple."""
    report = resolve_and_test_report(agent_type, store, secret_map, tests, cache=cache)
    return report.config, list(report.failed_required)


def resolve_and_test_report(
    agent_type: str,
    store: SecretStore,
    secret_map: SecretMap,
    tests: tuple[CredentialTest, ...],
    *,
    cache: PassCache | None = None,
) -> CredentialTestReport:
    """Resolve secrets, run applicable tests, and return activation evidence."""
    config = resolve_config(agent_type, store, secret_map)
    str_config = {k: v for k, v in config.items() if isinstance(v, str)}
    applicable: list[str] = []
    tested: list[str] = []
    passed: list[str] = []
    cached: list[str] = []
    failed_required: list[str] = []
    failed_optional: list[str] = []
    transport_failures: list[CredentialTransportFailure] = []
    for test in tests:
        if test.agent_types and agent_type not in test.agent_types:
            continue
        applicable.append(test.name)
        if test.cost == "costly" and cache is not None and cache.fresh(test.name):
            cached.append(test.name)
            continue
        tested.append(test.name)
        result = coerce_result(test.run(str_config))
        if result.status == "passed":
            passed.append(test.name)
            if test.cost == "costly" and cache is not None:
                cache.record(test.name)
        elif result.status == "transport_failure":
            transport_failures.append(
                CredentialTransportFailure(test.name, result.reason)
            )
        elif test.required:
            failed_required.append(test.name)
        else:
            failed_optional.append(test.name)
    return CredentialTestReport(
        config,
        tuple(applicable),
        tuple(tested),
        tuple(passed),
        tuple(cached),
        tuple(failed_required),
        tuple(failed_optional),
        tuple(transport_failures),
    )
