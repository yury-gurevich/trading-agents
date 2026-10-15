"""Choose the first declared LLM candidate whose probes pass (DL-289 P2, P3).

Agent: master
Role: probe an agent type's candidates in order, hand over the first that works and
      each later one that also works, as its fallbacks.
External I/O: none directly (delegates to the injected candidate probes).

A candidate passes when none of its required probes was refused and none went
unanswered. Every candidate is probed. The first that passes is chosen; each later
one that passes is handed over after it as a fallback, with its vendor's key, so the
role can move to it during the night (`DLIB-FAIL-05`). Every other candidate is
passed over: recorded, never a failure of the activation or of the fleet check. When
none passes, the first that was only unanswered is handed over unproven
(`MST-FAIL-04`) with no fallback; when every one was refused, every refusal stands
and the activation is refused.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.master.credential_outcomes import Outcomes
from kernel.llm_factory import KEY_ENV

if TYPE_CHECKING:
    from collections.abc import Mapping

    from agents.master.credential_check import CredentialTest, PassCache
    from agents.master.model_candidates import LlmCandidate, LlmRole

type Choice = tuple[Outcomes, str, tuple[str, ...], tuple[str, ...]]


def choose_llm(
    entries: list[tuple[CredentialTest, LlmCandidate, LlmRole]],
    config: dict[str, object],
    str_config: Mapping[str, str],
    cache: PassCache | None,
) -> Choice:
    """Return the outcomes, the chosen label, the passed over and the fallbacks."""
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
    chosen = next((item for item in tried if item[1].proven), None) or next(
        (item for item in tried if not item[1].failed_required), None
    )
    if chosen is None:
        refused = Outcomes()
        for _, outcomes in tried:
            refused.extend(outcomes)
        return refused, "", (), ()
    candidate, outcomes = chosen
    later = tried[tried.index(chosen) + 1 :]
    fallbacks = tuple(item for item, other in later if other.proven)
    report = Outcomes()
    report.extend(outcomes)
    for item, other in later:
        if item in fallbacks:
            report.extend(other)
    _hand_over(config, candidate, fallbacks, roles[candidate])
    passed_over = tuple(
        f"{item.label}: {other.first_reason()}"
        for item, other in tried
        if item != candidate and item not in fallbacks
    )
    return report, candidate.label, passed_over, tuple(f.label for f in fallbacks)


def _hand_over(
    config: dict[str, object],
    candidate: LlmCandidate,
    fallbacks: tuple[LlmCandidate, ...],
    role: LlmRole,
) -> None:
    """Name the candidate and its fallbacks; withhold every vendor's key none uses."""
    vendors = {candidate.vendor, *(item.vendor for item in fallbacks)}
    for vendor, key in KEY_ENV.items():
        if vendor not in vendors:
            config.pop(key, None)
    config[role.vendor_key] = candidate.vendor
    config[role.model_key] = candidate.model
    config[role.effort_key] = candidate.effort
    config[role.fallbacks_key] = ",".join(item.label for item in fallbacks)
