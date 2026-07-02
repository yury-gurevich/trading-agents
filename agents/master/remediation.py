"""Bounded remediation planning for credential-test failures.

Agent: master
Role: ask an injected LLM to select from a pack-supplied remediation catalogue
      and compute whether the selected plan is auto-eligible.
External I/O: reads remediation catalogue JSON when load_remediations is called;
      calls the injected LLMClient in select_remediation/plan_remediation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from kernel import LLMClient

FALLBACK_REMEDIATION = "pause-and-escalate"
_DEFAULT_RATIONALE = "Selected from the bounded remediation catalogue."


@dataclass(frozen=True)
class Remediation:
    """One vetted remediation option; metadata only in Piece C."""

    name: str
    description: str
    destructive: bool


@dataclass(frozen=True)
class RemediationPlan:
    """A planned remediation for an Escalation; execution happens in Piece D."""

    remediation: str
    rationale: str
    auto_eligible: bool
    status: str


def parse_remediations(text: str) -> tuple[Remediation, ...]:
    """Parse a remediation catalogue JSON array."""
    raw: object = json.loads(text)
    if not isinstance(raw, list):
        raise ValueError("remediation catalogue must be a JSON array")
    catalogue: list[Remediation] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("remediation entries must be JSON objects")
        name = item.get("name")
        description = item.get("description")
        destructive = item.get("destructive")
        if (
            not isinstance(name, str)
            or not isinstance(description, str)
            or not isinstance(destructive, bool)
        ):
            raise ValueError("remediation entries need name, description, destructive")
        if name in seen:
            raise ValueError(f"duplicate remediation {name!r}")
        seen.add(name)
        catalogue.append(Remediation(name, description, destructive))
    return tuple(catalogue)


def load_remediations(path: str) -> tuple[Remediation, ...]:
    """Load a remediation catalogue from a JSON file at *path*."""
    return parse_remediations(Path(path).read_text(encoding="utf-8"))


def select_remediation(
    failure: Mapping[str, object] | str,
    catalogue: Sequence[Remediation],
    llm: LLMClient,
) -> str:
    """Ask the LLM to choose one catalogue remediation; fallback on bad output."""
    return _select_with_rationale(failure, catalogue, llm)[0]


def plan_remediation(
    escalation: Mapping[str, object],
    catalogue: Sequence[Remediation],
    llm: LLMClient,
    *,
    scope: str,
    mode: str,
) -> RemediationPlan:
    """Plan a remediation and mark whether it can auto-run under the settings."""
    try:
        selected, rationale = _select_with_rationale(escalation, catalogue, llm)
    except Exception as exc:
        selected = FALLBACK_REMEDIATION
        rationale = f"Planner failed open to human review ({type(exc).__name__})."
    remediation = _find_remediation(catalogue, selected)
    auto_eligible = mode == "automatic" and (
        scope == "all" or not remediation.destructive
    )
    return RemediationPlan(
        remediation=remediation.name,
        rationale=rationale,
        auto_eligible=auto_eligible,
        status="planned",
    )


def _select_with_rationale(
    failure: Mapping[str, object] | str,
    catalogue: Sequence[Remediation],
    llm: LLMClient,
) -> tuple[str, str]:
    names = tuple(option.name for option in catalogue)
    raw = llm.complete(
        system=(
            "You are the master remediation planner. Choose exactly one remediation "
            "from the catalogue. Do not invent actions. Return JSON only."
        ),
        user=_user_prompt(failure, catalogue),
        tool_schema=_tool_schema(names),
    )
    parsed = _json_object(raw)
    if parsed is None:
        return FALLBACK_REMEDIATION, "Planner response was not valid JSON."
    choice = parsed.get("remediation")
    if not isinstance(choice, str) or choice not in names:
        return FALLBACK_REMEDIATION, "Planner choice was outside the catalogue."
    rationale = parsed.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        return choice, _DEFAULT_RATIONALE
    return choice, rationale.strip()


def _tool_schema(names: tuple[str, ...]) -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "remediation": {"type": "string", "enum": list(names)},
            "rationale": {"type": "string"},
        },
        "required": ["remediation", "rationale"],
        "additionalProperties": False,
    }


def _user_prompt(
    failure: Mapping[str, object] | str, catalogue: Sequence[Remediation]
) -> str:
    lines = [
        "Credential-test failure:",
        _failure_text(failure),
        "",
        "Remediation catalogue:",
    ]
    lines.extend(
        f"- {item.name} (destructive={item.destructive}): {item.description}"
        for item in catalogue
    )
    lines.append("")
    lines.append('Return JSON: {"remediation": <name>, "rationale": <why>}.')
    return "\n".join(lines)


def _failure_text(failure: Mapping[str, object] | str) -> str:
    if isinstance(failure, str):
        return failure
    return json.dumps(dict(failure), sort_keys=True, default=str)


def _json_object(raw: str) -> dict[str, object] | None:
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end < start:
        return None
    parsed: object = json.loads(raw[start : end + 1])
    assert isinstance(parsed, dict)
    return {str(key): value for key, value in parsed.items()}


def _find_remediation(catalogue: Sequence[Remediation], name: str) -> Remediation:
    for remediation in catalogue:
        if remediation.name == name:
            return remediation
    return Remediation(
        FALLBACK_REMEDIATION,
        "Pause automation and escalate to a human operator.",
        False,
    )
