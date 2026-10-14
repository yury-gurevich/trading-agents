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
from threading import Lock
from typing import TYPE_CHECKING, Literal

from agents.master.credential_outcomes import Outcomes
from agents.master.model_choice import choose_llm
from agents.master.secret_map import resolve_config

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from agents.master.credential_report import CredentialTestReport
    from agents.master.credential_result import CheckResult
    from agents.master.key_vault import SecretStore
    from agents.master.model_candidates import LlmCandidate, LlmRole
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
    transport failure is faulted by the caller but does not block. A test with a
    ``candidate`` probes that LLM candidate for an agent type that chooses one
    (DL-289); ``takes_candidate`` marks a declared probe able to carry one.
    """

    name: str
    run: Callable[[Mapping[str, str]], CheckResult]
    required: bool = True
    cost: Cost = "cheap"
    agent_types: tuple[str, ...] = ()
    llm_provider: str = ""
    takes_candidate: bool = False
    candidate: LlmCandidate | None = None
    role: LlmRole | None = None


class PassCache:
    """Remembers costly passes so a live call is skipped within the TTL (0 = never).

    Shared by concurrent activations and the preflight thread: the lock guards the
    map only, never a live probe, so a race costs a duplicate probe (DL-249 D4).
    """

    def __init__(
        self, ttl_minutes: int = 0, *, clock: Callable[[], datetime] | None = None
    ) -> None:
        """TTL cache in minutes (0 = never expires) with an injectable clock."""
        self._ttl = timedelta(minutes=ttl_minutes)
        self._never = ttl_minutes == 0
        self._clock = clock or (lambda: datetime.now(UTC))
        self._passes: dict[str, datetime] = {}
        self._lock = Lock()

    def fresh(self, name: str) -> bool:
        """Return True if *name* passed recently enough to skip a live re-test."""
        with self._lock:
            at = self._passes.get(name)
        if at is None:
            return False
        return self._never or (self._clock() - at) < self._ttl

    def record(self, name: str) -> None:
        """Remember that *name* passed now."""
        with self._lock:
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
    """Resolve secrets, run applicable tests, and return activation evidence.

    An agent type with LLM candidates runs its other tests first, then is handed
    the first candidate that passes (`model_choice`).
    """
    config = resolve_config(agent_type, store, secret_map)
    str_config = {k: v for k, v in config.items() if isinstance(v, str)}
    applicable = [
        test for test in tests if not test.agent_types or agent_type in test.agent_types
    ]
    outcomes = Outcomes()
    for test in applicable:
        if test.candidate is None:
            outcomes.run(test, str_config, cache)
    candidates = [
        (test, test.candidate, test.role)
        for test in applicable
        if test.candidate is not None and test.role is not None
    ]
    if not candidates:
        return outcomes.report(config)
    chosen, label, passed_over = choose_llm(candidates, config, str_config, cache)
    outcomes.extend(chosen)
    return outcomes.report(config, llm_candidate=label, llm_passed_over=passed_over)
