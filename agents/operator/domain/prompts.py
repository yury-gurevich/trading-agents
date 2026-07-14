"""Operator prompt and tool-schema builders.

Agent: operator
Role: build bounded LLM prompts from the declared intent grammar.
External I/O: none.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from agents.operator.domain.grammar import INTENT_FAMILIES

if TYPE_CHECKING:
    from contracts.operator import HumanCommand

FAMILY_NAMES = tuple(INTENT_FAMILIES)
INTENT_TOOL_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "outcome": {
            "type": "string",
            "enum": ["intent", "refused", "needs_clarification"],
        },
        "family": {"type": "string", "enum": list(FAMILY_NAMES)},
        "parameters": {"type": "object"},
        "reason": {"type": "string"},
    },
    "required": ["outcome"],
}


def build_interpret_system() -> str:
    """Build the bounded command-interpretation system prompt."""
    families = ", ".join(
        f"{name}: {spec.description}" for name, spec in INTENT_FAMILIES.items()
    )
    return (
        "Map the operator command to exactly one allowed trading-system intent, "
        "or refuse/ask for clarification. Questions about how a selected or past "
        "run performed are explain intents; status is only current whole-system "
        f"health. Allowed families: {families}."
    )


def build_interpret_user(command: HumanCommand) -> str:
    """Build the user prompt for one human command."""
    return (
        f"Command: {command.text}\nActor: {command.actor}\nChannel: {command.channel}"
    )


def build_explain_system() -> str:
    """Build the explanation-mode system prompt."""
    return (
        "Explain the requested system state using only the supplied graph evidence. "
        "Return one concise paragraph prioritizing the verdict, supporting numbers, "
        "and anything needing operator attention; do not repeat the evidence dump."
    )


def build_explain_user(subject: str, evidence: list[dict[str, object]]) -> str:
    """Build the explanation prompt with serialized evidence."""
    return f"Subject: {subject}\nEvidence: {json.dumps(evidence, sort_keys=True)}"
