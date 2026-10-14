"""Choose the first declared LLM candidate whose probes pass (DL-289 P2).

Agent: master
Role: try an agent type's candidates in order, hand over the first that works.
External I/O: none directly (delegates to the injected candidate probes).

A candidate passes when none of its required probes was refused and none went
unanswered. The ones before it are passed over: recorded, never a failure of the
activation or of the fleet check. When none passes, the first that was only
unanswered is handed over unproven (`MST-FAIL-04`); when every one was refused,
every refusal stands and the activation is refused.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.master.credential_outcomes import Outcomes
from kernel.llm_factory import KEY_ENV

if TYPE_CHECKING:
    from collections.abc import Mapping

    from agents.master.credential_test import CredentialTest, PassCache
    from agents.master.model_candidates import LlmCandidate, LlmRole


def choose_llm(
    entries: list[tuple[CredentialTest, LlmCandidate, LlmRole]],
    config: dict[str, object],
    str_config: Mapping[str, str],
    cache: PassCache | None,
) -> tuple[Outcomes, str, tuple[str, ...]]:
    """Return the outcomes to report, the chosen label and the passed-over lines."""
    groups: dict[LlmCandidate, list[CredentialTest]] = {}
    roles: dict[LlmCandidate, LlmRole] = {}
    for test, candidate, role in entries:
        groups.setdefault(candidate, []).append(test)
        roles[candidate] = role
    tried: list[tuple[LlmCandidate, Outcomes]] = []
    for candidate, group in groups.items():
        outcomes = Outcomes()
        for test in group:
            outcomes.run(test, str_config, cache)
        tried.append((candidate, outcomes))
        if outcomes.proven:
            break
    chosen = next((item for item in tried if item[1].proven), None) or next(
        (item for item in tried if not item[1].failed_required), None
    )
    if chosen is None:
        refused = Outcomes()
        for _, outcomes in tried:
            refused.extend(outcomes)
        return refused, "", ()
    candidate, outcomes = chosen
    _hand_over(config, candidate, roles[candidate])
    passed_over = tuple(
        f"{item.label}: {other.first_reason()}"
        for item, other in tried
        if item != candidate
    )
    return outcomes, candidate.label, passed_over


def _hand_over(
    config: dict[str, object], candidate: LlmCandidate, role: LlmRole
) -> None:
    """Name the candidate in the role's keys; withhold every other vendor's key."""
    for vendor, key in KEY_ENV.items():
        if vendor != candidate.vendor:
            config.pop(key, None)
    config[role.vendor_key] = candidate.vendor
    config[role.model_key] = candidate.model
    config[role.effort_key] = candidate.effort
