"""A debater turn carries its guided reading (S246 B3).

Agent: deliberator
Role: prove the defender and challenger ask for, parse and record the guided
      reasoning, and render the turn text the next speaker and the judge read.
External I/O: none.
"""

from __future__ import annotations

from agents.deliberator.agent import DeliberatorAgent
from agents.deliberator.settings import DeliberatorSettings
from agents.deliberator.tests.guided_fixtures import (
    EMPTY_REASONING,
    EXPECTED_EMPTY_TEXT,
    EXPECTED_TEXT,
    REASONING,
    VALID,
    RecordingLLM,
    completion,
)
from contracts.deliberator import (
    DebateProposition,
    DebateTurnRecord,
    DebateTurnReply,
    DebateTurnRequest,
)
from kernel import InMemoryGraphStore, InProcessBus
from kernel.deliberation import CHALLENGER_SYSTEM, DEFENDER_SYSTEM
from kernel.deliberation_guided import GuidedReasoning
from kernel.deliberation_program import ADAPTER, guided_program

_PROPOSITION = DebateProposition(decision="buy AAPL (qty 1)", context="pe: 30")


def _messages(prompt: str, transcript: str) -> tuple[str, str]:
    signature = guided_program(prompt).predict.signature
    return (
        ADAPTER.format_system_message(signature),
        ADAPTER.format_user_message_content(
            signature,
            {
                "decision": _PROPOSITION.decision,
                "context": _PROPOSITION.context,
                "transcript": transcript,
            },
            main_request=True,
        ),
    )


def _serve(role: str, llm: RecordingLLM, request: DebateTurnRequest) -> DebateTurnReply:
    agent = DeliberatorAgent(
        InProcessBus(),
        graph=InMemoryGraphStore(),
        llm=llm,
        settings=DeliberatorSettings(role=role),  # type: ignore[arg-type]
    )
    return agent.debate_turn(request)


def test_a_defender_turn_carries_its_guided_reading() -> None:
    """DLIB-OUT-06 / DLIB-TYP-01: the reasoning is typed, recorded, and rendered."""
    llm = RecordingLLM(VALID)
    request = DebateTurnRequest(
        request_id="r:AAPL:defender:r1",
        proposition=_PROPOSITION,
        role="defender",
        round_number=1,
    )

    reply = _serve("proponent", llm, request)

    assert reply.turn.reasoning == GuidedReasoning.model_validate(REASONING)
    assert reply.turn.reasoning_error is None
    assert reply.turn.text == EXPECTED_TEXT
    assert llm.calls == [_messages(DEFENDER_SYSTEM, "(none yet)")]


def test_a_challenger_turn_reads_the_transcript_and_carries_its_reading() -> None:
    """DLIB-OUT-06 / DLIB-TYP-01: the challenger is guided too, after the defender."""
    llm = RecordingLLM(completion(EMPTY_REASONING))
    request = DebateTurnRequest(
        request_id="r:AAPL:challenger:r1",
        proposition=_PROPOSITION,
        role="challenger",
        round_number=1,
        transcript=(DebateTurnRecord(role="defender", round=1, text="Holds.\nFirm."),),
    )

    reply = _serve("opponent", llm, request)

    assert reply.turn.reasoning == GuidedReasoning(readings=[], gaps=[])
    assert reply.turn.reasoning_error is None
    assert reply.turn.text == EXPECTED_EMPTY_TEXT
    assert llm.calls == [_messages(CHALLENGER_SYSTEM, "[defender r1] Holds.\nFirm.")]
