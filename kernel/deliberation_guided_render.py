"""Render the guided turn's messages and its recorded text, without DSPy.

Agent: kernel
Role: build DSPy's ChainOfThought system and user messages for a guided debate
      turn from the frozen format text, and render a parsed turn as the text the
      next speaker and the judge read (DL-252 D1, D2, D5).
External I/O: none.
"""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

from kernel.deliberation_guided_format import (
    GUIDED_TURN_PREFIX,
    GUIDED_USER_REQUIREMENTS,
    OBJECTIVE_LEAD,
)

if TYPE_CHECKING:
    from kernel.deliberation import Turn
    from kernel.deliberation_guided import GuidedReasoning


def guided_system(role_prompt: str) -> str:
    """Return DSPy's system message for this signature around one role prompt.

    As `ChatAdapter.format_task_description` does: the prompt is dedented, then
    every line, blank ones too, is put on its own line behind eight spaces.
    """
    lines = textwrap.dedent(role_prompt).splitlines()
    return GUIDED_TURN_PREFIX + OBJECTIVE_LEAD + ("\n" + " " * 8).join(["", *lines])


def guided_user(decision: str, context: str, transcript: str) -> str:
    """Return DSPy's user message for one turn's three inputs."""
    sections = (
        f"[[ ## decision ## ]]\n{decision}",
        f"[[ ## context ## ]]\n{context}",
        f"[[ ## transcript ## ]]\n{transcript}",
        GUIDED_USER_REQUIREMENTS,
    )
    return "\n\n".join(("", *sections, "")).strip()


def render_transcript(transcript: tuple[Turn, ...]) -> str:
    """Return the debate so far as the guided message's transcript input."""
    if not transcript:
        return "(none yet)"
    return "\n".join(f"[{turn.role} r{turn.round}] {turn.text}" for turn in transcript)


def render_guided_text(reasoning: GuidedReasoning, argument: str) -> str:
    """Return the turn text the next speaker and the judge read (DL-252 D2).

    Every value is printed exactly as the model copied it: no number formatting,
    because the other side and S247 must see the string the model wrote.
    """
    readings = [
        f"{item.metric} = {item.value}: {item.meaning_here} ({item.bears_on})"
        for item in reasoning.readings
    ]
    return "\n".join(
        (
            *_listed("Readings", readings),
            *_listed("Gaps", reasoning.gaps),
            f"Argument: {argument}",
        )
    )


def _listed(title: str, items: list[str]) -> tuple[str, ...]:
    if not items:
        return (f"{title}: none",)
    return (f"{title}:", *(f"- {item}" for item in items))
