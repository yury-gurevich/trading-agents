"""Deliberation prompt pipeline tests.

Agent: tooling
Role: verify the S119 compile and comparison scripts without network or DSPy.
External I/O: temporary prompt artifact and golden files.
"""

from __future__ import annotations

import json

from scripts.compare_deliberation_prompts import (
    _FakeReportLLM,
    compare_roles,
    format_table,
)
from scripts.compile_deliberation_prompts import compile_artifacts
from scripts.deliberation_eval import _CLASS1

from kernel import load_deliberation_prompt_artifacts


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
