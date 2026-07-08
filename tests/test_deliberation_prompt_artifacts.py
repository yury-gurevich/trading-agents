"""Deliberation prompt artifact tests.

Agent: kernel
Role: verify compiled deliberation role PromptArtifact parsing and composition.
External I/O: temporary filesystem writes for loader coverage.
"""

from __future__ import annotations

import json

import pytest

from kernel import (
    DEFAULT_DELIBERATION_PROMPTS,
    DELIBERATION_ROLE_FILENAMES,
    DELIBERATION_ROLE_TASKS,
    PromptArtifact,
    ensure_deliberation_artifact,
    load_deliberation_prompt_artifact,
    load_deliberation_prompt_artifacts,
    parse_prompt_artifact,
    prompts_from_artifacts,
)


def _artifact(role: str, *, prompt: str = "compiled") -> dict[str, object]:
    return {
        "task": DELIBERATION_ROLE_TASKS[role],
        "model": f"{role}-model",
        "version": "v1",
        "system_prompt": prompt,
        "examples": [],
    }


def _text(payload: dict[str, object]) -> str:
    return json.dumps(payload)


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {
            "task": "deliberation.defender",
            "model": "m",
            "version": "v",
            "system_prompt": "p",
            "examples": {},
        },
        {
            "task": "deliberation.defender",
            "model": "m",
            "version": "v",
            "system_prompt": "p",
            "examples": [{"inputs": [], "output": "x"}],
        },
        {
            "task": "deliberation.defender",
            "model": "m",
            "version": "v",
            "system_prompt": "p",
            "examples": [{"inputs": {}, "output": 1}],
        },
        {"task": 1, "model": "m", "version": "v", "system_prompt": "p"},
    ],
)
def test_parse_prompt_artifact_rejects_invalid_json(payload: object) -> None:
    with pytest.raises(ValueError, match="prompt artifact"):
        parse_prompt_artifact(json.dumps(payload))


def test_parse_prompt_artifact_accepts_examples() -> None:
    payload = _artifact("defender")
    payload["examples"] = [
        {"inputs": {"case": "x"}, "output": "safe", "rationale": "because"}
    ]

    artifact = parse_prompt_artifact(_text(payload))

    assert artifact.examples[0].inputs == {"case": "x"}
    assert artifact.examples[0].output == "safe"
    assert artifact.examples[0].rationale == "because"


def test_load_and_validate_one_deliberation_artifact(tmp_path) -> None:
    path = tmp_path / "prompt.json"
    path.write_text(_text(_artifact("judge")), encoding="utf-8")

    artifact = load_deliberation_prompt_artifact(path, "judge")

    assert artifact.task == "deliberation.judge"
    assert artifact.model == "judge-model"


def test_ensure_deliberation_artifact_rejects_wrong_task() -> None:
    artifact = PromptArtifact("deliberation.judge", "m", "v", "prompt", ())

    with pytest.raises(ValueError, match="defender prompt artifact"):
        ensure_deliberation_artifact(artifact, "defender")


@pytest.mark.parametrize(
    ("model", "prompt", "message"),
    [(" ", "prompt", "model"), ("m", " ", "system_prompt")],
)
def test_ensure_deliberation_artifact_requires_model_and_prompt(
    model: str, prompt: str, message: str
) -> None:
    artifact = PromptArtifact("deliberation.defender", model, "v", prompt, ())

    with pytest.raises(ValueError, match=message):
        ensure_deliberation_artifact(artifact, "defender")


def test_load_directory_and_compose_prompts(tmp_path) -> None:
    for role, filename in DELIBERATION_ROLE_FILENAMES.items():
        (tmp_path / filename).write_text(
            _text(_artifact(role, prompt=f"{role} compiled")),
            encoding="utf-8",
        )

    artifacts = load_deliberation_prompt_artifacts(tmp_path)
    prompts = prompts_from_artifacts(artifacts)

    assert prompts.defender == "defender compiled"
    assert prompts.challenger == "challenger compiled"
    assert prompts.judge == "judge compiled"


def test_prompts_from_artifacts_can_overlay_one_role() -> None:
    artifact = parse_prompt_artifact(_text(_artifact("challenger", prompt="compiled")))

    prompts = prompts_from_artifacts({"challenger": artifact})

    assert prompts.defender == DEFAULT_DELIBERATION_PROMPTS.defender
    assert prompts.challenger == "compiled"
    assert prompts.judge == DEFAULT_DELIBERATION_PROMPTS.judge


def test_prompts_from_artifacts_rejects_unknown_role() -> None:
    artifact = parse_prompt_artifact(_text(_artifact("defender")))

    with pytest.raises(ValueError, match="unknown deliberation role"):
        prompts_from_artifacts({"auditor": artifact})
