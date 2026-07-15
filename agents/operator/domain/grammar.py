"""Operator intent grammar and confirmation policy.

Agent: operator
Role: define allowed intent families and side-effect confirmation requirements.
External I/O: none.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contracts.operator import IntentFamily, TypedIntent


@dataclass(frozen=True)
class FamilySpec:
    """One allowed operator intent family."""

    description: str
    params: tuple[str, ...]
    requires_confirmation: bool


INTENT_FAMILIES: dict[IntentFamily, FamilySpec] = {
    "status": FamilySpec("read system status", (), False),
    "explain": FamilySpec("explain a decision or artifact", ("subject",), False),
    "approve": FamilySpec("approve a pending item", ("target",), True),
    "reject": FamilySpec("reject a pending item", ("target",), True),
    "modify": FamilySpec("change a parameter", ("name", "value"), True),
    "run": FamilySpec("start a trading run", ("stage",), True),
    "mode": FamilySpec("switch operating mode", ("mode",), True),
    "stage": FamilySpec("promote or demote execution stage", ("stage",), True),
    "pause": FamilySpec("pause scheduling", (), False),
    "resume": FamilySpec(
        "resume a selected run from one pipeline stage",
        ("run_id", "stage"),
        True,
    ),
}

_APPROVE_PATTERNS = (
    re.compile(r"^\s*(?:please\s+)?approve\s+(?P<target>\S.*?)\s*\.?\s*$", re.I),
    re.compile(
        r"^\s*(?:please\s+)?confirm\s+approval\s+(?:for|of)\s+"
        r"(?P<target>\S.*?)\s*\.?\s*$",
        re.I,
    ),
)


def normalize_explicit_intent(
    command_text: str, data: dict[str, object]
) -> dict[str, object]:
    """Pin explicit command grammar when the model picks a broader family."""
    target = _approve_target(command_text)
    if target is None:
        return data
    params = data.get("parameters", {})
    existing = params if isinstance(params, dict) else {}
    return {
        **data,
        "outcome": "intent",
        "family": "approve",
        "parameters": {**existing, "target": target},
    }


def apply_confirmation_policy(family: IntentFamily, intent: TypedIntent) -> TypedIntent:
    """Force confirmation policy from the grammar, ignoring model output."""
    return intent.model_copy(
        update={"requires_confirmation": INTENT_FAMILIES[family].requires_confirmation}
    )


def _approve_target(command_text: str) -> str | None:
    first_line = command_text.splitlines()[0] if command_text.splitlines() else ""
    for pattern in _APPROVE_PATTERNS:
        match = pattern.match(first_line)
        if match is not None:
            return match.group("target").strip()
    return None
