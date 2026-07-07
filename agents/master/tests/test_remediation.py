"""Remediation planner tests — DL-36 Piece C.

Agent: master
Role: verify bounded LLM remediation selection, auto-eligibility, and graph
      persistence for escalation plans.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from agents.master.remediation import (
    FALLBACK_REMEDIATION,
    Remediation,
    load_remediations,
    parse_remediations,
    plan_remediation,
    select_remediation,
)
from agents.master.tests.helpers import TRADING_REMEDIATIONS_PATH

if TYPE_CHECKING:
    from pathlib import Path

_CATALOGUE = (
    Remediation("refetch-from-key-vault", "Fetch the value again.", False),
    Remediation("rotate-credential", "Rotate the value.", True),
    Remediation(FALLBACK_REMEDIATION, "Escalate to a human.", False),
)


class _LLM:
    """Fake structured LLM with schema capture."""

    def __init__(self, response: str | Exception, expected_system: str = "") -> None:
        self.response = response
        self.expected_system = expected_system or "remediation planner"
        self.last_schema: dict[str, object] | None = None

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        assert self.expected_system in system
        assert "Credential-test failure" in user
        self.last_schema = tool_schema
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def _response(name: str, rationale: str = "The value is stale.") -> str:
    return f'{{"remediation": "{name}", "rationale": "{rationale}"}}'


def test_select_remediation_uses_enum_schema_and_valid_choice() -> None:
    llm = _LLM(_response("refetch-from-key-vault"))
    selected = select_remediation("postgres test failed", _CATALOGUE, llm)
    assert selected == "refetch-from-key-vault"
    assert llm.last_schema is not None
    props = cast("dict[str, object]", llm.last_schema["properties"])
    remediation = cast("dict[str, object]", props["remediation"])
    assert remediation["enum"] == [
        "refetch-from-key-vault",
        "rotate-credential",
        FALLBACK_REMEDIATION,
    ]


def test_select_remediation_uses_compiled_system_prompt() -> None:
    llm = _LLM(_response("refetch-from-key-vault"), "compiled champion")
    selected = select_remediation(
        "postgres test failed",
        _CATALOGUE,
        llm,
        system_prompt="compiled champion prompt",
    )
    assert selected == "refetch-from-key-vault"


@pytest.mark.parametrize(
    "raw",
    [
        _response("invent-a-new-action"),
        "not json",
    ],
)
def test_select_remediation_falls_back_on_bad_model_output(raw: str) -> None:
    assert select_remediation({"failed": ["postgres"]}, _CATALOGUE, _LLM(raw)) == (
        FALLBACK_REMEDIATION
    )


def test_plan_remediation_uses_default_rationale_when_model_omits_one() -> None:
    plan = plan_remediation(
        {"failed_credentials": ["postgres"]},
        _CATALOGUE,
        _LLM(_response("refetch-from-key-vault", "")),
        scope="safe_only",
        mode="automatic",
    )
    assert plan.remediation == "refetch-from-key-vault"
    assert plan.rationale == "Selected from the bounded remediation catalogue."


def test_plan_remediation_fails_open_when_llm_raises() -> None:
    plan = plan_remediation(
        {"failed_credentials": ["postgres"]},
        (Remediation("refetch-from-key-vault", "Fetch again.", False),),
        _LLM(RuntimeError("offline")),
        scope="all",
        mode="automatic",
    )
    assert plan.remediation == FALLBACK_REMEDIATION
    assert plan.auto_eligible is True
    assert "RuntimeError" in plan.rationale


@pytest.mark.parametrize(
    ("scope", "mode", "choice", "expected"),
    [
        ("safe_only", "automatic", "refetch-from-key-vault", True),
        ("safe_only", "automatic", "rotate-credential", False),
        ("all", "automatic", "rotate-credential", True),
        ("all", "manual", "refetch-from-key-vault", False),
    ],
)
def test_auto_eligible_truth_table(
    scope: str, mode: str, choice: str, expected: bool
) -> None:
    plan = plan_remediation(
        {"failed_credentials": ["postgres"]},
        _CATALOGUE,
        _LLM(_response(choice)),
        scope=scope,
        mode=mode,
    )
    assert plan.auto_eligible is expected
    assert plan.status == "planned"


def test_load_remediations_reads_pack_style_json(tmp_path: Path) -> None:
    path = tmp_path / "remediations.json"
    path.write_text(
        '[{"name":"resume-instance","description":"Resume it.","destructive":false}]',
        encoding="utf-8",
    )
    assert load_remediations(str(path)) == (
        Remediation("resume-instance", "Resume it.", False),
    )


def test_trading_remediation_pack_is_loadable() -> None:
    catalogue = load_remediations(TRADING_REMEDIATIONS_PATH)
    names = {item.name for item in catalogue}
    assert names == {
        "refetch-from-key-vault",
        "resume-instance",
        "rotate-credential",
        "recreate-instance",
        FALLBACK_REMEDIATION,
    }


@pytest.mark.parametrize(
    "text",
    [
        "{}",
        "[1]",
        '[{"name":"x","description":"missing destructive"}]',
        (
            '[{"name":"x","description":"one","destructive":false},'
            '{"name":"x","description":"two","destructive":false}]'
        ),
    ],
)
def test_parse_remediations_rejects_invalid_catalogues(text: str) -> None:
    with pytest.raises(ValueError, match=r"remediation|catalogue|duplicate"):
        parse_remediations(text)
