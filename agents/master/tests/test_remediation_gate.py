"""Remediation selector gate tests.

Agent: master
Role: verify the exact-match golden selector metric and compiled prompt artifacts.
External I/O: reads production remediation pack JSON fixtures.
"""

from __future__ import annotations

import pytest

from agents.master.remediation import Remediation, load_remediations
from agents.master.remediation_gate import (
    RemediationSelectionCase,
    check_selection_baseline,
    load_prompt_artifact,
    load_selection_cases,
    parse_selection_cases,
    passing_selection_names,
    prompt_examples,
    run_selection_eval,
    score_selection,
    selection_pass_rate,
)
from agents.master.tests.helpers import (
    TRADING_REMEDIATION_PROMPT_PATH,
    TRADING_REMEDIATION_SELECTION_CASES_PATH,
    TRADING_REMEDIATIONS_PATH,
)
from kernel import FakeLLMClient

_CATALOGUE = (
    Remediation("refetch-from-key-vault", "Fetch the value again.", False),
    Remediation("resume-instance", "Resume the instance.", False),
    Remediation("pause-and-escalate", "Ask a human.", False),
)


def _response(remediation: str) -> str:
    return f'{{"remediation": "{remediation}", "rationale": "matched"}}'


def _fake_llm() -> FakeLLMClient:
    return FakeLLMClient(
        {
            "blank-key-vault": _response("refetch-from-key-vault"),
            "neo4j-paused": _response("resume-instance"),
            "ambiguous": _response("pause-and-escalate"),
        }
    )


def _cases() -> tuple[RemediationSelectionCase, ...]:
    return (
        RemediationSelectionCase(
            "blank-key-vault-secret",
            {"summary": "blank-key-vault secret failed"},
            "refetch-from-key-vault",
            "Key Vault can be re-read safely.",
        ),
        RemediationSelectionCase(
            "paused-backing-instance",
            {"summary": "neo4j-paused backing instance"},
            "resume-instance",
            "Resume is safe.",
        ),
        RemediationSelectionCase(
            "ambiguous-unknown-failure",
            {"summary": "ambiguous failure"},
            "pause-and-escalate",
            "Unknown cases should stop.",
        ),
    )


def test_parse_selection_cases_accepts_labelled_json() -> None:
    parsed = parse_selection_cases(
        '[{"name":"case","failure":{"x":1},"expected":"safe","rationale":"why"}]'
    )
    assert parsed == (RemediationSelectionCase("case", {"x": 1}, "safe", "why"),)


@pytest.mark.parametrize(
    "text",
    [
        "{}",
        "[1]",
        '[{"name":"case","failure":[],"expected":"safe"}]',
    ],
)
def test_parse_selection_cases_rejects_invalid_json(text: str) -> None:
    with pytest.raises(ValueError, match="selection case"):
        parse_selection_cases(text)


def test_pack_selection_cases_and_prompt_are_loadable() -> None:
    cases = load_selection_cases(TRADING_REMEDIATION_SELECTION_CASES_PATH)
    artifact = load_prompt_artifact(TRADING_REMEDIATION_PROMPT_PATH)
    assert {case.name for case in cases} == {
        "blank-key-vault-secret",
        "paused-backing-instance",
        "compromised-credential",
        "destroyed-backing-service",
        "ambiguous-unknown-failure",
    }
    assert artifact.task == "remediation-selection"
    assert artifact.model == "gpt-5.5"
    assert len(artifact.examples) == len(cases)


def test_exact_match_metric_and_pass_rate() -> None:
    good = score_selection(_cases()[0], "refetch-from-key-vault")
    bad = score_selection(_cases()[1], "pause-and-escalate")
    assert good.passed is True
    assert bad.passed is False
    assert selection_pass_rate((good, bad)) == 0.5
    assert selection_pass_rate(()) == 0.0


def test_run_selection_eval_uses_compiled_prompt() -> None:
    scores = run_selection_eval(
        _fake_llm(),
        _cases(),
        _CATALOGUE,
        system_prompt="compiled remediation selector",
    )
    assert selection_pass_rate(scores) == 1.0
    assert passing_selection_names(scores) == frozenset(case.name for case in _cases())


def test_check_selection_baseline_reports_regression_and_gain() -> None:
    candidate = (
        score_selection(_cases()[0], "refetch-from-key-vault"),
        score_selection(_cases()[1], "pause-and-escalate"),
        score_selection(_cases()[2], "pause-and-escalate"),
    )
    check = check_selection_baseline(
        candidate,
        frozenset({"blank-key-vault-secret", "paused-backing-instance"}),
    )
    assert not check.passed
    assert check.regressed == ("paused-backing-instance",)
    assert check.gained == ("ambiguous-unknown-failure",)


def test_prompt_examples_preserve_failure_output_and_rationale() -> None:
    examples = prompt_examples(_cases())
    assert examples[0].inputs == {"summary": "blank-key-vault secret failed"}
    assert examples[0].output == "refetch-from-key-vault"
    assert examples[0].rationale == "Key Vault can be re-read safely."


def test_real_trading_catalogue_passes_offline_selector_cases() -> None:
    scores = run_selection_eval(
        FakeLLMClient(
            {
                "blank-key-vault-secret": _response("refetch-from-key-vault"),
                "neo4j-paused": _response("resume-instance"),
                "credential-compromised": _response("rotate-credential"),
                "service-destroyed": _response("recreate-instance"),
                "unknown": _response("pause-and-escalate"),
            }
        ),
        load_selection_cases(TRADING_REMEDIATION_SELECTION_CASES_PATH),
        load_remediations(TRADING_REMEDIATIONS_PATH),
        system_prompt=load_prompt_artifact(
            TRADING_REMEDIATION_PROMPT_PATH
        ).system_prompt,
    )
    assert selection_pass_rate(scores) == 1.0
