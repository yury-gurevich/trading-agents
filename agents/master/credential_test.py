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

    ``run(config)`` returns True when the credential works. A ``required`` failure
    blocks activation; a ``cost='costly'`` pass is cached (a live call costs money or
    submits an order, so it must not run on every activation).
    """

    name: str
    run: Callable[[Mapping[str, str]], bool]
    required: bool = True
    cost: Cost = "cheap"


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
    """Resolve the agent's secrets, run each test, return (config, failed_required).

    A costly test that passed recently (per ``cache``) is not re-run. A required test
    that fails names itself in the returned list; the caller (master.activate) refuses
    handover and escalates when that list is non-empty. Optional failures are
    non-blocking (activation proceeds).
    """
    config = resolve_config(agent_type, store, secret_map)
    str_config = {k: v for k, v in config.items() if isinstance(v, str)}
    failures: list[str] = []
    for test in tests:
        if test.cost == "costly" and cache is not None and cache.fresh(test.name):
            continue
        if test.run(str_config):
            if test.cost == "costly" and cache is not None:
                cache.record(test.name)
        elif test.required:
            failures.append(test.name)
    return config, failures
