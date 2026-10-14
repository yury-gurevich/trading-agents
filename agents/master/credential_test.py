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

from typing import TYPE_CHECKING

from agents.master.credential_check import Cost, CredentialTest, PassCache
from agents.master.credential_outcomes import Outcomes
from agents.master.model_choice import choose_llm
from agents.master.secret_map import resolve_config

if TYPE_CHECKING:
    from agents.master.credential_report import CredentialTestReport
    from agents.master.key_vault import SecretStore
    from agents.master.secret_map import SecretMap

# Re-exported: the two types live in `credential_check` so the modules this one imports
# can read them without importing it back (S276, a CodeQL unsafe cyclic import).
__all__ = [
    "ActivationRefused",
    "Cost",
    "CredentialTest",
    "PassCache",
    "resolve_and_test",
    "resolve_and_test_report",
]


class ActivationRefused(ValueError):  # noqa: N818 - a state ("refused"), not an *Error
    """A required credential failed its test — the agent must not be activated.

    Subclasses ValueError so the master HTTP server maps it to a 422 (the agent stays
    PRE_FLIGHT); the master records an Escalation before raising it.
    """


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
