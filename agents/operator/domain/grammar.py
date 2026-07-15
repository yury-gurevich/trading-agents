"""Operator intent grammar and confirmation policy.

Agent: operator
Role: define allowed intent families and side-effect confirmation requirements.
External I/O: none.
"""

from __future__ import annotations

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


def apply_confirmation_policy(family: IntentFamily, intent: TypedIntent) -> TypedIntent:
    """Force confirmation policy from the grammar, ignoring model output."""
    return intent.model_copy(
        update={"requires_confirmation": INTENT_FAMILIES[family].requires_confirmation}
    )
