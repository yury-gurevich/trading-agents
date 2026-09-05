"""Drive the five dependent batch rounds that replay a corpus of debates.

Agent: orchestration
Role: submit one batch per round, refuse answers it never asked for, and report
      how much was actually sent.
External I/O: none directly — the provider is reached through the injected
              BatchGateway, so this module is testable without spending money.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from orchestration.replay_rounds import (
    apply_results,
    build_states,
    plan_steps,
    round_requests,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence

    from orchestration.replay_types import (
        Arm,
        BatchRequest,
        BatchResult,
        DebateState,
        ReplaySubject,
        Step,
    )

__all__ = ["BatchGateway", "ReplayOutcome", "replay_debates"]


class BatchGateway(Protocol):
    """Submit one round and return its answers, in any order."""

    def run(self, requests: Sequence[BatchRequest]) -> tuple[BatchResult, ...]:
        """Return one result per request, keyed by custom_id."""
        ...  # pragma: no cover - protocol declaration only.


@dataclass(frozen=True)
class ReplayOutcome:
    """Every debate's final state, plus what it cost in requests."""

    states: tuple[DebateState, ...]
    rounds_submitted: int
    requests_submitted: int

    def completed(self) -> tuple[DebateState, ...]:
        """Debates that reached a verdict without a named failure."""
        return tuple(
            state
            for state in self.states
            if state.failure is None and state.verdict is not None
        )

    def failures(self) -> tuple[DebateState, ...]:
        """Debates excluded from every metric, each carrying its reason."""
        return tuple(state for state in self.states if state.failure is not None)


def replay_debates(
    subjects: Iterable[ReplaySubject],
    arms: Sequence[Arm],
    repeats: int,
    gateway: BatchGateway,
    *,
    on_round: Callable[[Step, int], None] | None = None,
) -> ReplayOutcome:
    """Replay every subject through every arm, one batch per debate round."""
    states = build_states(subjects, arms, repeats)
    rounds = 0
    sent = 0
    for step in plan_steps(arms):
        requests = round_requests(states, step)
        if on_round is not None:
            on_round(step, len(requests))
        if not requests:
            continue
        rounds += 1
        sent += len(requests)
        apply_results(states, step, _checked(requests, gateway.run(requests)))
    return ReplayOutcome(
        states=states, rounds_submitted=rounds, requests_submitted=sent
    )


def _checked(
    requests: Sequence[BatchRequest], results: Iterable[BatchResult]
) -> tuple[BatchResult, ...]:
    """Refuse an answer to a question this round never asked.

    A custom_id the round did not send means the gateway is mismapping results,
    and a mismapped transcript is worse than a missing one: it looks complete.
    """
    asked = {request.custom_id for request in requests}
    checked = tuple(results)
    stray = sorted({result.custom_id for result in checked} - asked)
    if stray:
        raise ValueError(f"batch returned unrequested custom_ids: {stray[:3]}")
    return checked
