"""Turn each LLM role's vendor probes into one probe per declared candidate.

Agent: master
Role: build, once at start, the ordered candidate probes an activation tries.
External I/O: none; pure transformation of injected pack data.

The master refuses to start when a role could not run on a candidate it declares:
no probe of that vendor for the agent type, a probe that cannot carry a model and
an effort, or no key of that vendor in the agent type's secret map.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from agents.master.credential_probe_candidate import with_candidate
from kernel.llm_factory import KEY_ENV

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from agents.master.credential_result import CheckResult
    from agents.master.credential_test import CredentialTest
    from agents.master.model_candidates import LlmCandidate, LlmPlan
    from agents.master.secret_map import SecretMap


def expand_llm_candidates(
    plan: LlmPlan | None,
    provider: str,
    tests: tuple[CredentialTest, ...],
    secret_map: SecretMap | None,
) -> tuple[CredentialTest, ...]:
    """Replace each role type's LLM probes with its candidates' probes, in order."""
    if plan is None:
        return tests
    kept = tuple(
        test
        for test in tests
        if not test.llm_provider or not set(test.agent_types) & set(plan.roles)
    )
    expanded: list[CredentialTest] = []
    for agent_type, role in plan.roles.items():
        granted = {env for _, env in (secret_map or {}).get(agent_type, [])}
        for candidate in plan.ordered(provider):
            probes = [
                test
                for test in tests
                if test.llm_provider == candidate.vendor
                and agent_type in test.agent_types
            ]
            _refuse_unrunnable(agent_type, candidate, probes, granted)
            expanded.extend(
                replace(
                    test,
                    name=f"{test.name}:{candidate.model}:{candidate.effort}",
                    run=_bound(test, candidate),
                    agent_types=(agent_type,),
                    candidate=candidate,
                    role=role,
                )
                for test in probes
            )
    return kept + tuple(expanded)


def _refuse_unrunnable(
    agent_type: str,
    candidate: LlmCandidate,
    probes: list[CredentialTest],
    granted: set[str],
) -> None:
    where = f"{agent_type} candidate {candidate.label}"
    if not probes:
        raise ValueError(f"{where} has no {candidate.vendor} probe")
    if not all(test.takes_candidate for test in probes):
        raise ValueError(f"{where} has a probe without candidate_paths")
    if KEY_ENV[candidate.vendor] not in granted:
        raise ValueError(f"{where} is not granted {KEY_ENV[candidate.vendor]}")


def _bound(
    test: CredentialTest, candidate: LlmCandidate
) -> Callable[[Mapping[str, str]], CheckResult]:
    def run(config: Mapping[str, str]) -> CheckResult:
        return test.run(with_candidate(config, candidate.model, candidate.effort))

    return run
