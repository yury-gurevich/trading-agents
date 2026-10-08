"""The guided turn's edges: unreadable, empty, the judge, the cap (S246 B4, B7, B10).

Agent: deliberator
Role: prove an unreadable reasoning keeps the raw turn, an empty completion still
      raises, the judge is asked and parsed exactly as before, and the output cap
      and its law row agree.
External I/O: reads agents/deliberator/laws/laws.md.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from agents.deliberator.agent import DeliberatorAgent
from agents.deliberator.settings import DeliberatorSettings
from agents.deliberator.tests.guided_fixtures import (
    EXPECTED_TEXT,
    UNREADABLE,
    RecordingLLM,
)
from contracts.deliberator import (
    DebateProposition,
    DebateTurnRecord,
    DebateTurnRequest,
    VerdictRequest,
)
from kernel import InMemoryGraphStore, InProcessBus, LLMCompletionStoppedError
from kernel.deliberation import (
    JUDGE_SYSTEM,
    Proposition,
    Turn,
    render_debate_prompt,
)

_PROPOSITION = DebateProposition(decision="buy AAPL (qty 1)", context="pe: 30")
_UPHOLD = '{"ruling": "overturn", "rationale": "stop inside one ATR"}'


def _agent(role: str, llm: RecordingLLM) -> DeliberatorAgent:
    return DeliberatorAgent(
        InProcessBus(),
        graph=InMemoryGraphStore(),
        llm=llm,
        settings=DeliberatorSettings(role=role),  # type: ignore[arg-type]
    )


def _request() -> DebateTurnRequest:
    return DebateTurnRequest(
        request_id="r:AAPL:defender:r1",
        proposition=_PROPOSITION,
        role="defender",
        round_number=1,
    )


_REASONS = {
    "bears_on_outside_enum": "schema: readings.0.bears_on: ",
    "missing_argument": "missing field: argument",
    "malformed_json_trailing_comma": "invalid JSON in reasoning: ",
    "no_sections": "missing field: reasoning, argument",
    "empty_argument": "empty field: argument",
}


@pytest.mark.parametrize("name", sorted(UNREADABLE))
def test_an_unreadable_reasoning_keeps_the_raw_turn_and_names_why(name: str) -> None:
    """DLIB-OUT-06 / DLIB-NEV-06: the turn is returned; the reason is recorded."""
    reply = _agent(
        "proponent", RecordingLLM(f"\n\n{UNREADABLE[name]}  \n")
    ).debate_turn(_request())

    assert reply.turn.text == UNREADABLE[name].strip()
    assert reply.turn.reasoning is None
    assert str(reply.turn.reasoning_error).startswith(_REASONS[name])
    assert reply.llm_call_key is not None


def test_an_empty_completion_still_raises() -> None:
    """DLIB-NEV-07: an empty turn is never recorded, guided or not."""
    agent = _agent("proponent", RecordingLLM("  \n "))

    with pytest.raises(LLMCompletionStoppedError, match="empty_debate_turn"):
        agent.debate_turn(_request())


def test_the_judge_is_asked_and_parsed_exactly_as_before() -> None:
    """DLIB-FAIL-04 / DLIB-TYP-03: the judge's prompt, message and parse are unchanged.

    🪤 What changes is the debater text it quotes: the rendered readings (B7).
    """
    llm = RecordingLLM("", judge_answer=_UPHOLD)
    transcript = (
        DebateTurnRecord(role="defender", round=1, text=EXPECTED_TEXT),
        DebateTurnRecord(role="challenger", round=1, text="raw, unreadable turn"),
    )

    reply = _agent("manager", llm).verdict(
        VerdictRequest(
            request_id="r:AAPL:judge", proposition=_PROPOSITION, transcript=transcript
        )
    )

    assert llm.calls == [
        (
            JUDGE_SYSTEM,
            render_debate_prompt(
                Proposition("buy AAPL (qty 1)", "pe: 30"),
                tuple(Turn(t.role, t.round, t.text) for t in transcript),
            ),
        )
    ]
    assert (reply.ruling, reply.rationale) == ("overturn", "stop inside one ATR")


def test_the_output_cap_is_16384_and_its_law_row_agrees() -> None:
    """DLIB-DEP-04: the default, its measured why, and the PARAM row say the same."""
    field = DeliberatorSettings.model_fields["max_tokens"]
    law = (Path(__file__).parents[1] / "laws" / "laws.md").read_text(encoding="utf-8")

    assert DeliberatorSettings().max_tokens == 16384
    assert DeliberatorSettings(max_tokens=16384).max_tokens == 16384
    with pytest.raises(ValidationError, match="max_tokens"):
        DeliberatorSettings(max_tokens=16385)
    for reason in ("3,026", "gpt-5.5", "reasoning", "7,738", "11,556", "unused cap"):
        assert reason in str(field.description)
    assert "| `max_tokens` | `16384` | int >= 64 <= 16384 | YES |" in law
