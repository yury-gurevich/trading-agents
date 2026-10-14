"""The credential check and the pass cache the master's tests are built from (DL-36).

Agent: master
Role: hold the two types every credential module reads, so `credential_outcomes` and
      `model_choice` read them without importing `credential_test`, which imports both
      of those back (a CodeQL unsafe cyclic import, S276); `credential_test` re-exports
      them, so every existing importer is unchanged.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from agents.master.credential_result import CheckResult
    from agents.master.model_candidates import LlmCandidate, LlmRole

Cost = Literal["cheap", "costly"]


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
