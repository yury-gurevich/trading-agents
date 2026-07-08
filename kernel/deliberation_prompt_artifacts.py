"""Deliberation prompt artifacts — parse opt-in compiled role prompts.

Agent: kernel
Role: load ADR-0010 PromptArtifact JSON for deliberation roles without importing
      agents, LLM providers, or DSPy.
External I/O: filesystem reads when loaders are used.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from kernel.deliberation import DEFAULT_DELIBERATION_PROMPTS, DeliberationPrompts
from kernel.optimizer import PromptArtifact, PromptExample

if TYPE_CHECKING:
    from collections.abc import Mapping

DELIBERATION_ROLES = ("defender", "challenger", "judge")
DELIBERATION_ROLE_TASKS = {
    "defender": "deliberation.defender",
    "challenger": "deliberation.challenger",
    "judge": "deliberation.judge",
}
DELIBERATION_ROLE_FILENAMES = {
    "defender": "deliberation_defender_prompt.json",
    "challenger": "deliberation_challenger_prompt.json",
    "judge": "deliberation_judge_prompt.json",
}


def _required_str(raw: Mapping[str, object], key: str) -> str:
    value = raw.get(key)
    if isinstance(value, str):
        return value
    raise ValueError("prompt artifact needs task/model/version/system_prompt")


def _parse_example(raw: object) -> PromptExample:
    if not isinstance(raw, dict) or not isinstance(raw.get("inputs"), dict):
        raise ValueError("prompt artifact examples need input objects")
    output = raw.get("output")
    rationale = raw.get("rationale", "")
    if not isinstance(output, str) or not isinstance(rationale, str):
        raise ValueError("prompt artifact examples need output/rationale")
    return PromptExample(dict(raw["inputs"]), output, rationale)


def parse_prompt_artifact(text: str) -> PromptArtifact:
    """Parse a compiled prompt artifact from JSON."""
    raw: object = json.loads(text)
    if not isinstance(raw, dict):
        raise ValueError("prompt artifact must be a JSON object")
    raw_examples = raw.get("examples", [])
    if not isinstance(raw_examples, list):
        raise ValueError("prompt artifact examples must be a list")
    return PromptArtifact(
        task=_required_str(raw, "task"),
        model=_required_str(raw, "model"),
        version=_required_str(raw, "version"),
        system_prompt=_required_str(raw, "system_prompt"),
        examples=tuple(_parse_example(item) for item in raw_examples),
    )


def load_prompt_artifact(path: str | Path) -> PromptArtifact:
    """Load a compiled prompt artifact from JSON."""
    return parse_prompt_artifact(Path(path).read_text(encoding="utf-8"))


def ensure_deliberation_artifact(artifact: PromptArtifact, role: str) -> PromptArtifact:
    """Validate that an artifact belongs to ``role`` and carries a model stamp."""
    expected = DELIBERATION_ROLE_TASKS[role]
    if artifact.task != expected:
        raise ValueError(f"{role} prompt artifact must use task {expected!r}")
    if not artifact.model.strip():
        raise ValueError("prompt artifact needs a non-empty model")
    if not artifact.system_prompt.strip():
        raise ValueError("prompt artifact needs a non-empty system_prompt")
    return artifact


def load_deliberation_prompt_artifact(path: str | Path, role: str) -> PromptArtifact:
    """Load and validate one deliberation role prompt artifact."""
    return ensure_deliberation_artifact(load_prompt_artifact(path), role)


def load_deliberation_prompt_artifacts(
    directory: str | Path,
) -> dict[str, PromptArtifact]:
    """Load all role prompt artifacts from a directory."""
    root = Path(directory)
    return {
        role: load_deliberation_prompt_artifact(
            root / DELIBERATION_ROLE_FILENAMES[role], role
        )
        for role in DELIBERATION_ROLES
    }


def prompts_from_artifacts(
    artifacts: Mapping[str, PromptArtifact],
    base: DeliberationPrompts = DEFAULT_DELIBERATION_PROMPTS,
) -> DeliberationPrompts:
    """Compose role prompts by overlaying validated artifacts on a base bundle."""
    prompts = {
        "defender": base.defender,
        "challenger": base.challenger,
        "judge": base.judge,
    }
    for role, artifact in artifacts.items():
        if role not in prompts:
            raise ValueError(f"unknown deliberation role {role!r}")
        prompts[role] = ensure_deliberation_artifact(artifact, role).system_prompt
    return DeliberationPrompts(
        defender=prompts["defender"],
        challenger=prompts["challenger"],
        judge=prompts["judge"],
    )
