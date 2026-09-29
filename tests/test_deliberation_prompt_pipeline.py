"""Deliberation prompt pipeline tests.

Agent: tooling
Role: verify the S119 compile and comparison scripts without network or DSPy.
External I/O: temporary prompt artifact and golden files.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.compare_deliberation_prompts import (
    _FakeReportLLM,
    compare_roles,
    format_table,
)
from scripts.compile_deliberation_prompts import compile_artifacts
from scripts.deliberation_eval import _CLASS1

from kernel import (
    CHALLENGER_SYSTEM,
    DELIBERATION_ROLES,
    JUDGE_SYSTEM,
    load_deliberation_prompt_artifacts,
)

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _shape(prompt: str) -> tuple[int, int, int]:
    return len(prompt), prompt.count("Compiled calibration"), prompt.count("Examples:")


def test_the_champion_is_its_sources_rebuilt(tmp_path) -> None:
    """DLIB-NEV-09 (A2): re-running the pipeline reproduces the promoted challenger
    and judge champions and all three committed artifacts byte for byte, with the
    calibration and the examples once each. Before S245 it started from the
    promoted constants and doubled them (13,023 vs 6,764 chars)."""
    compile_artifacts(
        debate_model="any-model",
        judge_model="any-model",
        version="rebuild",
        output_dir=tmp_path,
        dspy_module=object(),
    )
    rebuilt = load_deliberation_prompt_artifacts(tmp_path)
    committed = load_deliberation_prompt_artifacts(_SCRIPTS)

    for role, champion in (("challenger", CHALLENGER_SYSTEM), ("judge", JUDGE_SYSTEM)):
        assert _shape(rebuilt[role].system_prompt) == _shape(champion), role
        assert rebuilt[role].system_prompt == champion, role
    for role in DELIBERATION_ROLES:
        assert _shape(rebuilt[role].system_prompt)[1:] == (1, 1), role
        assert rebuilt[role].system_prompt == committed[role].system_prompt, role
        assert rebuilt[role].examples == committed[role].examples, role


def test_compile_deliberation_prompts_writes_role_artifacts(tmp_path) -> None:
    written = compile_artifacts(
        debate_model="gpt-5.5",
        judge_model="claude-opus-4-8",
        version="test-v1",
        output_dir=tmp_path,
        dspy_module=object(),
    )

    artifacts = load_deliberation_prompt_artifacts(tmp_path)

    assert set(written) == {"defender", "challenger", "judge"}
    assert artifacts["defender"].task == "deliberation.defender"
    assert artifacts["defender"].model == "gpt-5.5"
    assert artifacts["judge"].task == "deliberation.judge"
    assert artifacts["judge"].model == "claude-opus-4-8"
    assert len(artifacts["challenger"].examples) == len(_CLASS1) + 2


def test_compile_deliberation_prompts_can_write_one_role(tmp_path) -> None:
    written = compile_artifacts(
        debate_model="gpt-5.5",
        judge_model="claude-opus-4-8",
        version="test-v1",
        output_dir=tmp_path,
        roles=("challenger",),
        dspy_module=object(),
    )

    assert written == {"challenger": tmp_path / "deliberation_challenger_prompt.json"}
    assert not (tmp_path / "deliberation_defender_prompt.json").exists()
    assert not (tmp_path / "deliberation_judge_prompt.json").exists()


def test_compare_deliberation_prompts_fake_path_passes(tmp_path) -> None:
    compile_artifacts(
        debate_model="gpt-5.5",
        judge_model="claude-opus-4-8",
        version="test-v1",
        output_dir=tmp_path,
        dspy_module=object(),
    )
    golden = tmp_path / "golden.json"
    golden.write_text(
        json.dumps(
            {
                "passing": [
                    "alpha158-weight-zero",
                    "calendar-staleness",
                    "lightgbm-shadow",
                    "pooled-sigma",
                ]
            }
        ),
        encoding="utf-8",
    )
    fake = _FakeReportLLM()

    comparisons = compare_roles(
        artifacts=load_deliberation_prompt_artifacts(tmp_path),
        debate_llm=fake,
        debate_judge_llm=fake,
        scorer_judge_llm=fake,
        rounds=1,
        repeats=2,
        threshold=0.5,
        golden_path=golden,
    )
    table = format_table(comparisons)

    assert len(comparisons) == 3
    assert all(row.challenger.firewall_passed for row in comparisons)
    assert "| defender |" in table
    assert "PASS" in table
