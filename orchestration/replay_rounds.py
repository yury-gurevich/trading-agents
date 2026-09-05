"""The round machinery for replaying recorded debates through the Batch API.

Agent: orchestration
Role: turn a corpus of stored propositions into one batch per debate round, and
      fold each round's answers back into the transcripts the next round reads.
External I/O: none — requests are built here and submitted elsewhere.

A debate cannot be one batch of five requests: ``render_debate_prompt``
interpolates the transcript, so turn N+1's prompt contains turn N's answer
(DL-158). The five turns are sequential *within* a debate and independent
*across* debates, which is why a round — not a debate — is the batch unit.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from kernel.deliberation import (
    CHALLENGER_SYSTEM,
    DEFENDER_SYSTEM,
    JUDGE_SYSTEM,
    Turn,
    judge_verdict,
    render_debate_prompt,
)
from orchestration.replay_types import (
    ARGUING_ROLES,
    JUDGE_ROLE,
    BatchRequest,
    DebateState,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from kernel.deliberation import Verdict
    from orchestration.replay_types import Arm, BatchResult, ReplaySubject, Step

__all__ = ["apply_results", "build_states", "plan_steps", "round_requests"]

_SYSTEMS = {
    "defender": DEFENDER_SYSTEM,
    "challenger": CHALLENGER_SYSTEM,
    JUDGE_ROLE: JUDGE_SYSTEM,
}


def build_states(
    subjects: Iterable[ReplaySubject], arms: Sequence[Arm], repeats: int
) -> tuple[DebateState, ...]:
    """One state per subject x repeat x arm, each carrying its own step list."""
    return tuple(
        DebateState(subject=subject, repeat=repeat, arm=arm, steps=arm.steps())
        for subject in subjects
        for repeat in range(1, max(1, repeats) + 1)
        for arm in arms
    )


def plan_steps(arms: Sequence[Arm]) -> tuple[Step, ...]:
    """The submission order covering every arm, judge last for all of them."""
    rounds = max((max(1, arm.max_rounds) for arm in arms), default=0)
    if not rounds:
        return ()
    steps: list[Step] = [
        (role, number) for number in range(1, rounds + 1) for role in ARGUING_ROLES
    ]
    steps.append((JUDGE_ROLE, 0))
    return tuple(steps)


def round_requests(
    states: Iterable[DebateState], step: Step
) -> tuple[BatchRequest, ...]:
    """Build this round's requests for every debate still running."""
    requests = tuple(
        BatchRequest(
            custom_id=state.key(step).custom_id(),
            model=state.arm.model,
            max_tokens=state.arm.max_tokens,
            effort=state.arm.effort,
            system=_SYSTEMS[step[0]],
            user=render_debate_prompt(state.subject.proposition, state.transcript),
        )
        for state in _participants(states, step)
    )
    # Two states that address the same turn would share one answer, and the loser
    # would silently inherit the winner's transcript. Refuse the plan instead.
    if len({request.custom_id for request in requests}) != len(requests):
        raise ValueError(f"round {step} plans the same turn twice")
    return requests


def apply_results(
    states: Iterable[DebateState], step: Step, results: Iterable[BatchResult]
) -> None:
    """Fold one round's answers into the transcripts, naming every failure."""
    answers = {result.custom_id: result for result in results}
    for state in _participants(states, step):
        _apply_one(state, step, answers.get(state.key(step).custom_id()))


def _participants(states: Iterable[DebateState], step: Step) -> list[DebateState]:
    return [state for state in states if state.failure is None and step in state.steps]


def _apply_one(state: DebateState, step: Step, result: BatchResult | None) -> None:
    if result is None:
        state.failure = "missing_result"
        return
    if result.status != "succeeded":
        state.failure = result.status
        return
    text = result.text.strip()
    if not text:
        # The live path raises LLMCompletionStoppedError on an empty turn; here
        # the debate is excluded rather than fabricated.
        state.failure = "empty_turn"
        return
    role, number = step
    if role == JUDGE_ROLE:
        state.verdict = _verdict(state, text)
        return
    state.transcript = (*state.transcript, Turn(role, number, text))


def _verdict(state: DebateState, text: str) -> Verdict:
    """Rule with the live path's own parser, so replay cannot parse differently."""
    return judge_verdict(
        _Answered(text), state.subject.proposition, transcript=state.transcript
    )


class _Answered:
    """An LLMClient that has already been asked; it only replays the answer."""

    def __init__(self, text: str) -> None:
        self._text = text

    def complete(self, *, system: str, user: str, tool_schema: object) -> str:
        """Return the batch answer, ignoring the prompt that was already sent."""
        del system, user, tool_schema
        return self._text
