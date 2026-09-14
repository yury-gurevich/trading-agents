"""Refuse a remediation posture this image cannot actually honour.

Agent: master
Role: turn an inert operator switch into a loud one.
External I/O: none.

🚨 Item 41. `remediation_mode="automatic"` reads as a documented operator
control, and until now it was not one. `build_app` constructs `MasterAgent` with
no remediation LLM, catalogue, prompt or executors — it cannot, because the
catalogue lives in `orchestration` and import-linter forbids `agents ->
orchestration` (S86, [DL-12]). `plan_and_try_remediation` then meets
`if llm is None or not catalogue: return None`: no attempt, no `Escalation` note,
no flag. Flipping the switch changed nothing in the fleet and said nothing about
having changed nothing.

🪤 The fix is the noise, not the wiring. Pieces C/D of the DL-36 arc are
deliberately unbuilt ([DL-144]), so this refuses at construction — the same move
`build_app` already makes three lines earlier for a secret map that arrives with
no credential tests. Master laws are silent on remediation entirely, which is
recorded as [DRIFT-059] rather than answered with a premature clause.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.master.settings import MasterSettings

AUTOMATIC = "automatic"
_REFUSAL = (
    "remediation_mode='automatic' cannot be honoured by this entrypoint: no "
    "remediation catalogue or LLM is wired here (DL-144 pieces C/D are unbuilt), "
    "so automatic remediation would silently do nothing. Set "
    "MASTER_REMEDIATION_MODE=manual."
)


def refuse_unwired_automatic_remediation(settings: MasterSettings) -> None:
    """Raise when automatic remediation is asked for but cannot be performed."""
    if settings.remediation_mode != AUTOMATIC:
        return
    raise ValueError(_REFUSAL)
