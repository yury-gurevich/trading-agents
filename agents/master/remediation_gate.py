"""Eval gate for bounded remediation selection.

Agent: master
Role: score failure->remediation selector outputs against a labelled golden set.
External I/O: reads eval cases/prompt artifacts from JSON files when loaders are used.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from agents.master.remediation import Remediation, select_remediation
from kernel.deliberation_gate import BaselineCheck
from kernel.optimizer import PromptArtifact, PromptExample

if TYPE_CHECKING:
    from collections.abc import Sequence

    from kernel import LLMClient


@dataclass(frozen=True)
class RemediationSelectionCase:
    """One labelled selector eval case."""

    name: str
    failure: dict[str, object]
    expected: str
    rationale: str


@dataclass(frozen=True)
class RemediationSelectionScore:
    """Exact-match score for one remediation-selection case."""

    name: str
    expected: str
    selected: str
    passed: bool


def parse_selection_cases(text: str) -> tuple[RemediationSelectionCase, ...]:
    """Parse remediation-selection cases from JSON pack data."""
    raw: object = json.loads(text)
    if not isinstance(raw, list):
        raise ValueError("selection cases must be a JSON array")
    cases: list[RemediationSelectionCase] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("selection case entries must be JSON objects")
        name = item.get("name")
        failure = item.get("failure")
        expected = item.get("expected")
        rationale = item.get("rationale", "")
        if (
            not isinstance(name, str)
            or not isinstance(failure, dict)
            or not isinstance(expected, str)
            or not isinstance(rationale, str)
        ):
            raise ValueError("selection cases need name, failure, expected")
        cases.append(RemediationSelectionCase(name, failure, expected, rationale))
    return tuple(cases)


def load_selection_cases(path: str) -> tuple[RemediationSelectionCase, ...]:
    """Load remediation-selection cases from a JSON file."""
    return parse_selection_cases(Path(path).read_text(encoding="utf-8"))


def score_selection(
    case: RemediationSelectionCase, selected: str
) -> RemediationSelectionScore:
    """Exact-match metric: the selected remediation must equal the label."""
    return RemediationSelectionScore(
        name=case.name,
        expected=case.expected,
        selected=selected,
        passed=selected == case.expected,
    )


def run_selection_eval(
    llm: LLMClient,
    cases: Sequence[RemediationSelectionCase],
    catalogue: Sequence[Remediation],
    *,
    system_prompt: str = "",
) -> tuple[RemediationSelectionScore, ...]:
    """Run the selector once over each labelled case."""
    return tuple(
        score_selection(
            case,
            select_remediation(
                case.failure, catalogue, llm, system_prompt=system_prompt
            ),
        )
        for case in cases
    )


def selection_pass_rate(scores: Sequence[RemediationSelectionScore]) -> float:
    """Return the fraction of exact-match cases passed."""
    if not scores:
        return 0.0
    return sum(1 for score in scores if score.passed) / len(scores)


def passing_selection_names(
    scores: Sequence[RemediationSelectionScore],
) -> frozenset[str]:
    """Return cases the selector passed."""
    return frozenset(score.name for score in scores if score.passed)


def check_selection_baseline(
    candidate: Sequence[RemediationSelectionScore],
    golden_passing: frozenset[str],
) -> BaselineCheck:
    """Trip if a candidate regresses on a golden-passed case."""
    candidate_passing = passing_selection_names(candidate)
    return BaselineCheck(
        regressed=tuple(sorted(golden_passing - candidate_passing)),
        gained=tuple(sorted(candidate_passing - golden_passing)),
        passed=golden_passing <= candidate_passing,
    )


def prompt_examples(
    cases: Sequence[RemediationSelectionCase],
) -> tuple[PromptExample, ...]:
    """Convert labelled cases into optimizer examples."""
    return tuple(
        PromptExample(case.failure, case.expected, case.rationale) for case in cases
    )


def parse_prompt_artifact(text: str) -> PromptArtifact:
    """Parse a compiled prompt artifact from JSON."""
    raw: object = json.loads(text)
    if not isinstance(raw, dict):
        raise ValueError("prompt artifact must be a JSON object")
    task = raw.get("task")
    model = raw.get("model")
    version = raw.get("version")
    system_prompt = raw.get("system_prompt")
    raw_examples = raw.get("examples", [])
    if not (
        isinstance(task, str)
        and isinstance(model, str)
        and isinstance(version, str)
        and isinstance(system_prompt, str)
        and isinstance(raw_examples, list)
    ):
        raise ValueError("prompt artifact needs task/model/version/system_prompt")
    examples: list[PromptExample] = []
    for item in raw_examples:
        if not isinstance(item, dict) or not isinstance(item.get("inputs"), dict):
            raise ValueError("prompt artifact examples need input objects")
        output = item.get("output")
        rationale = item.get("rationale", "")
        if not isinstance(output, str) or not isinstance(rationale, str):
            raise ValueError("prompt artifact examples need output/rationale")
        examples.append(PromptExample(dict(item["inputs"]), output, rationale))
    return PromptArtifact(
        task=task,
        model=model,
        version=version,
        system_prompt=system_prompt,
        examples=tuple(examples),
    )


def load_prompt_artifact(path: str) -> PromptArtifact:
    """Load a compiled prompt artifact from JSON."""
    return parse_prompt_artifact(Path(path).read_text(encoding="utf-8"))
