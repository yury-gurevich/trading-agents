"""Remediation prompt artifact tests.

Agent: master
Role: verify compiled remediation prompt artifact parsing and fixture sanity.
External I/O: reads the production remediation selection-case fixture.
"""

from __future__ import annotations

import pytest

from agents.master.remediation_gate import (
    load_selection_cases,
    parse_prompt_artifact,
)
from agents.master.tests.helpers import TRADING_REMEDIATION_SELECTION_CASES_PATH


@pytest.mark.parametrize(
    "text",
    [
        "[]",
        '{"task":"t","model":"m","version":"v","system_prompt":"p","examples":{}}',
        (
            '{"task":"t","model":"m","version":"v","system_prompt":"p",'
            '"examples":[{"inputs":[],"output":"x"}]}'
        ),
        (
            '{"task":"t","model":"m","version":"v","system_prompt":"p",'
            '"examples":[{"inputs":{},"output":1}]}'
        ),
    ],
)
def test_parse_prompt_artifact_rejects_invalid_json(text: str) -> None:
    with pytest.raises(ValueError, match="prompt artifact"):
        parse_prompt_artifact(text)


def test_parse_prompt_artifact_accepts_examples() -> None:
    artifact = parse_prompt_artifact(
        '{"task":"t","model":"m","version":"v","system_prompt":"p",'
        '"examples":[{"inputs":{"x":1},"output":"safe","rationale":"why"}]}'
    )
    assert artifact.examples[0].inputs == {"x": 1}
    assert artifact.examples[0].output == "safe"


def test_no_case_name_duplicates_in_fixture() -> None:
    names = [
        case.name
        for case in load_selection_cases(TRADING_REMEDIATION_SELECTION_CASES_PATH)
    ]
    assert len(set(names)) == 5
