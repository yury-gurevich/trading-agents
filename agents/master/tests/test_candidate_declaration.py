"""A8-A9: candidate declarations are ordered, validated pack data.

Agent: master
Role: prove parse refusals and stable provider grouping.
External I/O: committed declaration read only.
"""

import json

import pytest

from agents.master.model_candidates import load_llm_plan, parse_llm_plan
from agents.master.tests.candidate_testkit import FIRST, PACKS, SECOND

GOOD = {"vendor": "openai", "model": "gpt-5.5", "effort": "high"}


def test_a8_real_declaration_parses_and_orders() -> None:
    """MST-OUT-05: real candidates, role keys and provider groups are explicit."""
    plan = load_llm_plan(str(PACKS / "trading_llm.json"))
    assert [item.label for item in plan.candidates] == [FIRST, SECOND]
    assert [item.label for item in plan.ordered("")] == [FIRST, SECOND]
    assert [item.label for item in plan.ordered("anthropic")] == [SECOND, FIRST]
    assert set(plan.roles) == {
        "deliberator-manager",
        "deliberator-proponent",
        "deliberator-opponent",
    }
    for agent_type, model_key in (
        ("deliberator-manager", "DELIBERATOR_JUDGE_MODEL"),
        ("deliberator-proponent", "DELIBERATOR_DEFENDER_MODEL"),
        ("deliberator-opponent", "DELIBERATOR_CHALLENGER_MODEL"),
    ):
        role = plan.roles[agent_type]
        assert role.vendor_key == "DELIBERATOR_LLM_PROVIDER"
        assert role.model_key == model_key
        assert role.effort_key == "DELIBERATOR_EFFORT"
    raw = json.loads((PACKS / "trading_llm.json").read_text("utf-8"))
    raw["candidates"].extend(
        [
            {"vendor": "openai", "model": "gpt-extra", "effort": "low"},
            {"vendor": "anthropic", "model": "claude-extra", "effort": "high"},
        ]
    )
    extended = parse_llm_plan(json.dumps(raw))
    assert [item.model for item in extended.ordered("anthropic")] == [
        "claude-opus-5",
        "claude-extra",
        "gpt-5.5",
        "gpt-extra",
    ]


@pytest.mark.parametrize(
    ("raw", "cause"),
    [
        ([], "must be an object"),
        ({}, "non-empty candidates"),
        ({"candidates": []}, "non-empty candidates"),
        ({"candidates": {}}, "non-empty candidates"),
        ({"candidates": ["bad"]}, "candidate must be an object"),
        ({"candidates": [GOOD | {"vendor": "opnai"}]}, "unknown.*vendor"),
        ({"candidates": [GOOD | {"model": "claude-opus-5"}]}, "belongs to anthropic"),
        ({"candidates": [GOOD | {"vendor": "anthropic"}]}, "belongs to openai"),
        ({"candidates": [GOOD | {"effort": ""}]}, "effort.*non-empty string"),
        ({"candidates": [{"vendor": "openai", "model": "gpt-5.5"}]}, "effort"),
        ({"candidates": [GOOD | {"model": None}]}, "model.*non-empty string"),
        ({"candidates": [GOOD | {"vendor": 7}]}, "vendor.*non-empty string"),
        ({"candidates": [GOOD, GOOD]}, "must not repeat"),
        ({"candidates": [GOOD], "roles": []}, "roles must map"),
        ({"candidates": [GOOD], "roles": {"role": []}}, "role.*must be an object"),
        (
            {
                "candidates": [GOOD],
                "roles": {"role": {"vendor": "", "model": "MODEL", "effort": "EFFORT"}},
            },
            "vendor.*non-empty string",
        ),
    ],
)
def test_a9_unrunnable_declaration_is_refused(raw: object, cause: str) -> None:
    """MST-NEV-08: malformed fields, foreign models and repeats name their cause."""
    with pytest.raises(ValueError, match=cause):
        parse_llm_plan(json.dumps(raw))


def test_a9_unknown_model_family_is_the_vendors_to_judge() -> None:
    """MST-NEV-08: an unfamiliar model family is accepted for the vendor's probe."""
    plan = parse_llm_plan(json.dumps({"candidates": [GOOD | {"model": "custom"}]}))
    assert plan.candidates[0].model == "custom"
    assert plan.roles == {}
