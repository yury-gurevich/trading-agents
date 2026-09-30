"""No known falsehood about our code reaches a debate role (S245, DL-251).

Agent: tooling
Role: pin the negative half of DLIB-NEV-09: no champion role prompt and no
      committed prompt artifact carries the claims S245 removed, nothing in
      `scripts/` builds an instruction from the promoted champions, the golden
      names only live cases, and every parameter a role is shown exists.
External I/O: reads the committed prompt artifacts, the golden file and the
      `scripts/` sources.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest
from scripts.deliberation_eval import _CLASS1
from tests.deliberation_fact_probes import anomalous

from agents.portfolio_manager.settings import PortfolioManagerSettings
from agents.provider.settings import ProviderSettings
from kernel.deliberation_prompts import (
    CHALLENGER_SYSTEM,
    DEFENDER_SYSTEM,
    JUDGE_SYSTEM,
)

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
_ROLES = ("defender", "challenger", "judge")
_CHAMPIONS = {"CHALLENGER_SYSTEM", "JUDGE_SYSTEM"}
_EXAMPLE_PARAMETERS = re.compile(r"\(e\.g\. ([^)]*)\)")
# Where each parameter a role prompt names as an example is a live setting.
_PARAMETER_HOMES = {
    "max_daily_move_sigma": ProviderSettings,
    "base_min_confidence": ProviderSettings,
    "max_sector_pct": PortfolioManagerSettings,
}
# The false or stale claims S245 removed (DRIFT-092). The word "calendar" is not
# banned: a calendar window or a calendar-gated check is a true statement.
_FALSE_CLAIMS = (
    "counts CALENDAR days",
    "calendar-day staleness",
    "calendar-day counting",
    "post-holiday recheck",
    "GICS-SECTOR cap",
    "NO name-correlation",
    '"calendar-staleness"',
    '"name-correlation"',
)


def _artifact_texts(role: str) -> list[str]:
    path = _SCRIPTS / f"deliberation_{role}_prompt.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    texts = [raw["system_prompt"]]
    for item in raw["examples"]:
        texts += [json.dumps(item["inputs"]), item["output"], item["rationale"]]
    return texts


def _shipped_texts() -> dict[str, list[str]]:
    shipped = {
        "DEFENDER_SYSTEM": [DEFENDER_SYSTEM],
        "CHALLENGER_SYSTEM": [CHALLENGER_SYSTEM],
        "JUDGE_SYSTEM": [JUDGE_SYSTEM],
    }
    for role in _ROLES:
        shipped[f"deliberation_{role}_prompt.json"] = _artifact_texts(role)
    return shipped


def test_no_false_fact_reaches_a_role() -> None:
    """DLIB-NEV-09 (A1): no champion constant, and no committed artifact's system
    prompt or example (inputs, output, rationale), states a claim S245 removed:
    the staleness gate has counted trading sessions since S87 (DL-10), and the
    portfolio has a measured correlation penalty (PM laws v1.3). Case-insensitive."""
    hits = sorted(
        {
            (source, claim)
            for source, texts in _shipped_texts().items()
            for text in texts
            for claim in _FALSE_CLAIMS
            if claim.lower() in text.lower()
        }
    )

    assert hits == []


def test_no_script_builds_from_the_promoted_champions() -> None:
    """DLIB-NEV-09 / DL-251 D5 (doubling guard): the compile pipeline starts from
    its sources. A script reading the promoted challenger or judge constant would
    nest the calibration and the examples twice, as S119's pipeline did."""
    readers = sorted(
        {
            path.name
            for path in _SCRIPTS.rglob("*.py")
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
            if (isinstance(node, ast.alias) and node.name in _CHAMPIONS)
            or (isinstance(node, ast.Attribute) and node.attr in _CHAMPIONS)
            or (isinstance(node, ast.Name) and node.id in _CHAMPIONS)
        }
    )

    assert readers == []


def test_the_golden_names_only_live_cases() -> None:
    """DLIB-NEV-09 / ADR-0010 (A8): every name in the golden's passing set and its
    fractions is a current Class-1 case. `check_robust` reports a golden name the
    candidate lacks as regressed, so a removed case would trip the firewall."""
    golden_path = _SCRIPTS / "deliberation_golden.json"
    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    live = {str(case[0]) for case in _CLASS1}

    assert set(golden["passing"]) <= live
    assert set(golden["fractions"]) <= live


@pytest.mark.parametrize(
    "prompt", [DEFENDER_SYSTEM, CHALLENGER_SYSTEM], ids=["defender", "challenger"]
)
def test_every_parameter_a_role_is_shown_is_a_live_setting(prompt: str) -> None:
    """DLIB-NEV-09 (DL-251 D5): the parameters a role prompt names as examples of
    this system's parameters are exactly the mapped ones, and each is a field of
    the agent settings that declares it today. The defender's text is unchanged."""
    match = _EXAMPLE_PARAMETERS.search(prompt)
    assert match is not None
    named = {name.strip() for name in match.group(1).split(",")}

    assert named == set(_PARAMETER_HOMES)
    assert all(name in home.model_fields for name, home in _PARAMETER_HOMES.items())


def test_the_same_nine_percent_is_excluded_on_a_calm_session() -> None:
    """PROV-OUT-09 (DL-251, beyond A3): the pooled-sigma example's "one 9% name does
    not trip it" holds on an ordinary session only. Among 98 names at +/-0.5 % the
    same +9 % is 8.7 sigma and excluded. Reported for work-queue 75/97; the
    example's text is unchanged."""
    assert anomalous(109.0, spread=0.5) == ("X",)
