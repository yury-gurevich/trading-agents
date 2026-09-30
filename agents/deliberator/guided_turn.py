"""Guided defender and challenger turns.

Agent: deliberator
Role: ask a debating role for its guided reasoning and argument, in DSPy's format
      rendered without DSPy, and turn the completion into the recorded turn.
External I/O: the LLM, through the injected client (the caller's ledger).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.deliberator import DebateTurnRecord
from kernel.deliberation import CHALLENGER_SYSTEM, DEFENDER_SYSTEM, Turn
from kernel.deliberation_guided import (
    GuidedTurn,
    guided_system,
    guided_user,
    parse_guided_turn,
    render_guided_text,
    render_transcript,
    unreadable,
)
from kernel.llm import LLMCompletionStoppedError

if TYPE_CHECKING:
    from contracts.deliberator import DebateTurnRequest
    from kernel.llm import LLMClient

#: One frozen system string per debating role, offered to the prompt cache as
#: the free-text prompts were (DLIB-OBS-06).
GUIDED_SYSTEMS = {
    "defender": guided_system(DEFENDER_SYSTEM),
    "challenger": guided_system(CHALLENGER_SYSTEM),
}


def guided_turn(llm: LLMClient, request: DebateTurnRequest) -> DebateTurnRecord:
    """Return one guided turn, its reasoning recorded or why it was not (DLIB-OUT-06).

    An empty completion still raises, as every debate turn did before
    (`DLIB-NEV-07`). An unreadable reasoning does not: the raw completion is kept
    as the turn's text and the reason is named, so neither the turn nor the order
    fails over how the model formatted what it wrote.
    """
    transcript = tuple(Turn(t.role, t.round, t.text) for t in request.transcript)
    completion = llm.complete(
        system=GUIDED_SYSTEMS[request.role],
        user=guided_user(
            request.proposition.decision,
            request.proposition.context,
            render_transcript(transcript),
        ),
        tool_schema={},
    )
    raw = completion.strip()
    if not raw:
        raise LLMCompletionStoppedError(
            provider="kernel", stop_reason="empty_debate_turn"
        )
    parsed = _with_argument(parse_guided_turn(completion))
    if parsed.reasoning is None or not parsed.argument:
        return DebateTurnRecord(
            role=request.role,
            round=request.round_number,
            text=raw,
            reasoning_error=parsed.error,
        )
    return DebateTurnRecord(
        role=request.role,
        round=request.round_number,
        text=render_guided_text(parsed.reasoning, parsed.argument),
        reasoning=parsed.reasoning,
    )


def _with_argument(parsed: GuidedTurn) -> GuidedTurn:
    """A blank argument is no argument: `Argument: ` alone is an empty turn."""
    if parsed.error is None and not parsed.argument:
        return unreadable("empty field: argument")
    return parsed
