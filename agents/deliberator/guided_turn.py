"""Guided defender and challenger turns executed by DSPy.

Agent: deliberator
Role: run the role's program and preserve the recorded turn's existing semantics.
External I/O: the injected LLM client, through the caller's ledger.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.deliberator import DebateTurnRecord
from kernel.deliberation import CHALLENGER_SYSTEM, DEFENDER_SYSTEM, Turn
from kernel.deliberation_guided_render import render_guided_text, render_transcript
from kernel.deliberation_program import ADAPTER, UnreadableTurnError, guided_program
from kernel.dspy_engine import run_program

if TYPE_CHECKING:
    from contracts.deliberator import DebateTurnRequest
    from kernel.llm import LLMClient

# Reuse programs, but bind the caller's client only inside a per-call context.
PROGRAMS = {
    "defender": guided_program(DEFENDER_SYSTEM),
    "challenger": guided_program(CHALLENGER_SYSTEM),
}


def guided_turn(llm: LLMClient, request: DebateTurnRequest) -> DebateTurnRecord:
    """Return the reasoning or its unreadability, without a second call."""
    transcript = tuple(Turn(t.role, t.round, t.text) for t in request.transcript)
    try:
        prediction = run_program(
            PROGRAMS[request.role],
            llm,
            adapter=ADAPTER,
            empty_stop_reason="empty_debate_turn",
            decision=request.proposition.decision,
            context=request.proposition.context,
            transcript=render_transcript(transcript),
        )
    except UnreadableTurnError as exc:
        return DebateTurnRecord(
            role=request.role,
            round=request.round_number,
            text=exc.completion.strip(),
            reasoning_error=exc.reason,
        )
    return DebateTurnRecord(
        role=request.role,
        round=request.round_number,
        text=render_guided_text(prediction.reasoning, prediction.argument),
        reasoning=prediction.reasoning,
    )
