"""Render the guided turn's recorded text and transcript.

Agent: kernel
Role: render a parsed turn as the text the next speaker and judge read (DL-252).
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel.deliberation import Turn
    from kernel.deliberation_guided import GuidedReasoning


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
