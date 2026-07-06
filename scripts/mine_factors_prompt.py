"""Prompt and parser helpers for governed factor mining.

Agent: tooling
Role: render the bounded factor catalogue and parse hostile selector JSON.
External I/O: none.
"""

from __future__ import annotations

import json

from agents.researcher.domain.factors import (
    CATALOGUE,
    FactorSelection,
    validate_selection,
)


def selection_from_text(text: str) -> FactorSelection | None:
    """Parse one hostile selector response into a validated selection."""
    parsed = _json_object(text)
    if parsed is None or set(parsed) != {"name", "params", "rationale"}:
        return None
    name = parsed["name"]
    params = parsed["params"]
    rationale = parsed["rationale"]
    if not isinstance(name, str) or not isinstance(params, dict):
        return None
    if not isinstance(rationale, str):
        return None
    return validate_selection(name, params, rationale=rationale.strip())


def selection_prompt() -> str:
    """Render the bounded catalogue prompt."""
    lines = ["Catalogue:"]
    for spec in CATALOGUE.values():
        params = ", ".join(
            f"{name}: {param.minimum:g}..{param.maximum:g} {param.unit}"
            for name, param in spec.parameters.items()
        )
        lines.append(f"- {spec.name}: {spec.summary} Params: {params}.")
    lines.append("")
    lines.append(
        'Return JSON: {"name": <factor>, "params": {...}, "rationale": <why>}.'
    )
    return "\n".join(lines)


def tool_schema() -> dict[str, object]:
    """Return the selector's bounded JSON schema."""
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string", "enum": list(CATALOGUE)},
            "params": {"type": "object"},
            "rationale": {"type": "string"},
        },
        "required": ["name", "params", "rationale"],
        "additionalProperties": False,
    }


def params_object(text: str) -> dict[str, object] | None:
    """Parse manual params JSON into an object map."""
    try:
        parsed: object = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _json_object(raw: str) -> dict[str, object] | None:
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end < start:
        return None
    try:
        parsed: object = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    return {str(key): value for key, value in parsed.items()}
