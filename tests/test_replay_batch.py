"""Batch driver tests.

Agent: tooling
Role: prove the driver sends one batch per round, in order, and refuses an
      answer it never asked for.
External I/O: none — the gateway is a fake.
"""

from __future__ import annotations

import pytest
from tests.replay_fixtures import CONTROL, ONE_ROUND, ScriptedGateway, subject

from orchestration.replay_batch import replay_debates
from orchestration.replay_types import BatchResult


def test_a_debate_is_replayed_as_five_dependent_rounds() -> None:
    """DL-158: the transcript makes turn N+1 depend on turn N's answer."""
    gateway = ScriptedGateway({})
    outcome = replay_debates([subject()], [CONTROL], 1, gateway)

    assert outcome.rounds_submitted == 5
    assert outcome.requests_submitted == 5
    assert len(gateway.rounds) == 5


def test_every_debate_of_one_round_travels_in_a_single_batch() -> None:
    """Debates are independent across subjects; that is the batching win."""
    gateway = ScriptedGateway({})
    replay_debates([subject("USB"), subject("AVGO")], [CONTROL], 2, gateway)

    assert [len(sent) for sent in gateway.rounds] == [4, 4, 4, 4, 4]


def test_a_completed_debate_carries_a_verdict_and_no_failure() -> None:
    """A verdict is the unit every later metric counts."""
    outcome = replay_debates([subject()], [CONTROL], 1, ScriptedGateway({}))

    assert len(outcome.completed()) == 1
    assert outcome.failures() == ()
    assert outcome.completed()[0].verdict is not None


def test_results_are_matched_by_custom_id_not_by_arrival_order() -> None:
    """The Batch API returns results in any order; the fake reverses them."""
    gateway = ScriptedGateway({"defender": "argued for", "challenger": "argued back"})
    outcome = replay_debates([subject("USB"), subject("AVGO")], [ONE_ROUND], 1, gateway)

    for state in outcome.completed():
        assert [turn.role for turn in state.transcript] == ["defender", "challenger"]
        assert state.transcript[0].text == "argued for"


def test_an_answer_to_a_question_this_round_never_asked_is_refused() -> None:
    """A mismapped transcript looks complete, which is worse than a missing one."""
    with pytest.raises(ValueError, match="unrequested custom_ids"):
        replay_debates([subject()], [CONTROL], 1, _StrayGateway())


def test_a_failed_debate_stops_costing_money_from_the_next_round_on() -> None:
    """The sweep's price is per request, so a void debate must stop sending."""
    outcome = replay_debates([subject()], [CONTROL], 1, _SilentGateway())

    assert outcome.rounds_submitted == 1
    assert outcome.requests_submitted == 1
    assert [state.failure for state in outcome.failures()] == ["missing_result"]


def test_the_caller_can_watch_each_round_before_it_is_submitted() -> None:
    """A sweep that spends real money must be observable while it runs."""
    seen: list[tuple[tuple[str, int], int]] = []
    replay_debates(
        [subject()],
        [ONE_ROUND],
        1,
        ScriptedGateway({}),
        on_round=lambda step, count: seen.append((step, count)),
    )

    assert seen == [(("defender", 1), 1), (("challenger", 1), 1), (("judge", 0), 1)]


def test_a_sweep_with_no_subjects_submits_no_batches_at_all() -> None:
    """An empty corpus must cost nothing, not one empty round per step."""
    gateway = ScriptedGateway({})
    outcome = replay_debates([], [CONTROL], 1, gateway)

    assert outcome.rounds_submitted == 0
    assert gateway.rounds == []


class _StrayGateway:
    """A gateway that answers with an id nobody asked for."""

    def run(self, requests: object) -> tuple[BatchResult, ...]:
        """Return one plausible-looking but unrequested answer."""
        del requests
        return (BatchResult("some-other-turn", "succeeded", "text"),)


class _SilentGateway:
    """A gateway that accepts the round and returns nothing."""

    def run(self, requests: object) -> tuple[BatchResult, ...]:
        """Return no answers at all."""
        del requests
        return ()
