"""Supervisor hard-NO safety surface.

Agent: supervisor
Role: permanently refuse unsafe intents before confirmation or routing.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contracts.operator import TypedIntent


def is_hard_no(intent: TypedIntent) -> tuple[bool, str]:
    """Return whether an intent is permanently forbidden."""
    params = intent.parameters
    # Live trading is blocked until explicit P8 stage-gate implementation.
    if params.get("stage") == "live" and intent.family == "run":
        return True, "live-stage trading is not enabled in this build phase"
    # A caller must never bypass the central capability gate.
    if params.get("bypass_gate") == "true":
        return True, "bypassing the capability gate is permanently forbidden"
    # The supervisor itself is part of the safety boundary and cannot be disabled.
    if params.get("disable_supervisor") == "true":
        return True, "disabling the supervisor is permanently forbidden"
    return False, ""
