"""Round machinery tests.

Agent: tooling
Role: prove a round batches what it should, and that a failed turn is named
      rather than fabricated.
External I/O: none.
"""

from __future__ import annotations

import pytest
from tests.replay_fixtures import CONTROL, ONE_ROUND, subject, verdict_json

from kernel.deliberation import CHALLENGER_SYSTEM, DEFENDER_SYSTEM, JUDGE_SYSTEM
from orchestration.replay_rounds import (
    apply_results,
    build_states,
    plan_steps,
    round_requests,
)
from orchestration.replay_types import BatchResult, DebateState

_R1 = ("defender", 1)
_JUDGE = ("judge", 0)


def test_a_round_is_the_batch_unit_because_turns_depend_on_each_other() -> None:
    """Every arm speaks defender then challenger per round, judge last."""
    assert CONTROL.steps() == (
        ("defender", 1),
        ("challenger", 1),
        ("defender", 2),
        ("challenger", 2),
        ("judge", 0),
    )


def test_the_plan_covers_the_longest_arm_and_judges_everyone_at_the_end() -> None:
    """A one-round arm idles through later rounds; it does not judge early."""
    assert plan_steps([ONE_ROUND, CONTROL]) == CONTROL.steps()


def test_a_plan_with_no_arms_submits_nothing() -> None:
    """An empty sweep is a no-op, not a round of zero requests."""
    assert plan_steps([]) == ()


def test_every_subject_repeat_and_arm_gets_its_own_transcript() -> None:
    """Repeats are what make self-agreement measurable; they must not share."""
    states = build_states([subject("USB"), subject("AVGO")], [CONTROL, ONE_ROUND], 3)

    assert len(states) == 12
    assert len({state.key(_R1).custom_id() for state in states}) == 12


def test_a_shorter_arm_sits_out_the_rounds_it_does_not_speak() -> None:
    """Arm C's whole point is fewer rounds, so it must send fewer requests."""
    states = build_states([subject()], [ONE_ROUND], 1)

    assert round_requests(states, ("defender", 2)) == ()
    assert len(round_requests(states, _R1)) == 1


def test_each_role_is_sent_the_system_prompt_the_live_path_uses() -> None:
    """A replay under a different system prompt measures a different thing."""
    states = build_states([subject()], [CONTROL], 1)
    systems = {
        step: round_requests(states, step)[0].system
        for step in (_R1, ("challenger", 1), _JUDGE)
    }

    assert systems[_R1] == DEFENDER_SYSTEM
    assert systems[("challenger", 1)] == CHALLENGER_SYSTEM
    assert systems[_JUDGE] == JUDGE_SYSTEM


def test_a_later_turn_sees_the_transcript_the_earlier_turn_produced() -> None:
    """This dependency is why five rounds cannot collapse into one batch."""
    states = build_states([subject()], [CONTROL], 1)
    apply_results(states, _R1, _answers(states, _R1, "the defence"))

    assert (
        "[defender r1] the defence" in round_requests(states, ("challenger", 1))[0].user
    )


def test_the_arm_carries_its_model_effort_and_token_cap_onto_the_wire() -> None:
    """The sweep varies these, so a request that drops them measures nothing."""
    request = round_requests(build_states([subject()], [CONTROL], 1), _R1)[0]

    assert (request.model, request.effort, request.max_tokens) == (
        "claude-opus-5",
        "high",
        4096,
    )


def test_a_round_that_plans_the_same_turn_twice_is_refused() -> None:
    """Two states sharing one answer would silently share one transcript."""
    twin = build_states([subject()], [CONTROL], 1)[0]
    states = (twin, DebateState(twin.subject, twin.repeat, twin.arm, steps=twin.steps))

    with pytest.raises(ValueError, match="same turn twice"):
        round_requests(states, _R1)


def test_the_judge_verdict_is_parsed_by_the_live_parser() -> None:
    """Replay must not be more forgiving of a malformed ruling than production."""
    states = _judged(verdict_json("overturn", "the gate never fired"))

    assert states[0].verdict is not None
    assert states[0].verdict.ruling == "overturn"


def test_an_unparseable_ruling_defaults_to_revise_exactly_as_it_does_live() -> None:
    """DLIB-TYP-03: replay must not admit a ruling the live parser would refuse."""
    states = _judged("not json at all")

    assert states[0].verdict is not None
    assert states[0].verdict.ruling == "revise"


def test_a_missing_answer_fails_the_debate_instead_of_skipping_the_turn() -> None:
    """A transcript with a hole is worse than an excluded debate."""
    states = build_states([subject()], [CONTROL], 1)
    apply_results(states, _R1, ())

    assert states[0].failure == "missing_result"
    assert states[0].transcript == ()


def test_a_provider_failure_is_recorded_under_its_own_name() -> None:
    """'expired' and 'errored' are different problems and must stay different."""
    states = build_states([subject()], [CONTROL], 1)
    request = round_requests(states, _R1)[0]
    apply_results(states, _R1, [BatchResult(request.custom_id, "expired")])

    assert states[0].failure == "expired"


def test_an_empty_answer_is_a_failure_not_an_empty_turn() -> None:
    """The live path raises on an empty turn; replay must not accept one."""
    states = build_states([subject()], [CONTROL], 1)
    apply_results(states, _R1, _answers(states, _R1, "   "))

    assert states[0].failure == "empty_turn"


def test_a_failed_debate_takes_no_further_part_in_the_sweep() -> None:
    """Continuing a broken transcript would spend money on a void result."""
    states = build_states([subject()], [CONTROL], 1)
    apply_results(states, _R1, ())

    assert round_requests(states, ("challenger", 1)) == ()


def _answers(
    states: tuple[DebateState, ...], step: tuple[str, int], text: str
) -> tuple[BatchResult, ...]:
    return tuple(
        BatchResult(request.custom_id, "succeeded", text)
        for request in round_requests(states, step)
    )


def _judged(text: str) -> tuple[DebateState, ...]:
    states = build_states([subject()], [ONE_ROUND], 1)
    for step in (_R1, ("challenger", 1)):
        apply_results(states, step, _answers(states, step, f"said at {step}"))
    apply_results(states, _JUDGE, _answers(states, _JUDGE, text))
    return states
