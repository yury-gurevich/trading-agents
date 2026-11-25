"""The judge rules on evidence specific to an order.

Agent: deliberator
Role: pin the judge contract, worked rulings, and prompt provenance.
External I/O: reads the committed judge prompt artifact.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import cast

import pytest
from scripts.deliberation_prompt_sources import JUDGE_CONTRAST_CASES, JUDGE_ORDER_RULE

from agents.deliberator.prompt_recipe import PROMPT_MODULES
from kernel.deliberation_prompts import (
    CHALLENGER_SYSTEM,
    DEFENDER_SYSTEM,
    JUDGE_SYSTEM,
)

_ROOT = Path(__file__).resolve().parents[1]


def _examples() -> list[dict[str, object]]:
    artifact = json.loads(
        (_ROOT / "scripts/deliberation_judge_prompt.json").read_text(encoding="utf-8")
    )
    return artifact["examples"]


def test_the_judge_is_told_to_rule_on_this_order() -> None:
    """DLIB-OUT-09: the champion directs an order-specific ruling."""
    assert JUDGE_ORDER_RULE.strip() in JUDGE_SYSTEM
    assert "cannot decide the ruling" in JUDGE_SYSTEM
    assert "do not uphold the decision" not in JUDGE_SYSTEM


def test_every_ruling_is_demonstrated() -> None:
    """DLIB-OUT-09: every committed example reaches the champion verbatim."""
    examples = _examples()
    rulings = Counter(
        json.loads(str(example["output"]))["ruling"] for example in examples
    )
    assert rulings == {"revise": 7, "uphold": 2, "overturn": 2}
    for example in examples:
        assert f"expected_output={example['output']}" in JUDGE_SYSTEM


def test_each_contrast_case_shows_its_ruling() -> None:
    """DLIB-OUT-09: each hypothetical demonstrates its specified ruling."""
    expected = {
        "shared-disclosed-figure": "uphold",
        "shared-sizing-rule": "uphold",
        "one-pillar-clearance": "revise",
        "wrong-price-input": "overturn",
        "stated-limit-broken": "overturn",
    }
    assert {case[0]: case[3] for case in JUDGE_CONTRAST_CASES} == expected
    by_case = {
        cast("dict[str, str]", example["inputs"])["case"]: json.loads(
            str(example["output"])
        )["ruling"]
        for example in _examples()
    }
    assert {name: by_case[name] for name in expected} == expected


@pytest.mark.parametrize("prompt", [DEFENDER_SYSTEM, CHALLENGER_SYSTEM])
def test_the_contrast_cases_reach_only_the_judge(prompt: str) -> None:
    """DLIB-OUT-09: the contrast examples never steer a debater."""
    for case in JUDGE_CONTRAST_CASES:
        assert case[0] not in prompt


def test_the_judge_prompt_is_in_the_recipe() -> None:
    """DLIB-OBS-07: the digest includes the module that holds the judge text."""
    assert "kernel.deliberation_judge_prompt" in {m.__name__ for m in PROMPT_MODULES}
