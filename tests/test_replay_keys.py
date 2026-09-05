"""Replay identity tests.

Agent: tooling
Role: prove a batch answer can only ever be attributed to the turn that asked.
External I/O: none.
"""

from __future__ import annotations

import re

from orchestration.replay_keys import JUDGE_ROUND, ReplayKey

_WIRE_SAFE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _key(**overrides: object) -> ReplayKey:
    fields: dict[str, object] = {
        "pm_run": "pm-run-5c9c98f0",
        "ticker": "USB",
        "repeat": 1,
        "arm": "control",
        "role": "defender",
        "round": 1,
    }
    fields.update(overrides)
    return ReplayKey(**fields)  # type: ignore[arg-type]


def test_the_label_carries_every_field_the_sweep_varies() -> None:
    """A label that hides the arm or the repeat cannot be read back."""
    assert _key().label() == "pm-run-5c9c98f0:USB:1:control:defender:r1"


def test_the_judge_turn_is_round_zero_and_says_so() -> None:
    """The judge speaks after the rounds, so it belongs to none of them."""
    assert _key(role="judge", round=JUDGE_ROUND).label().endswith(":judge:r0")


def test_the_wire_id_is_accepted_by_the_batch_api_charset() -> None:
    """A colon-separated label is not a legal custom_id; the wire id is."""
    assert _WIRE_SAFE.match(_key().custom_id())


def test_two_turns_that_differ_only_after_truncation_still_differ() -> None:
    """Truncating the readable half must not merge two distinct turns."""
    long_run = "pm-run-" + "a" * 60
    first = _key(pm_run=long_run, role="defender")
    second = _key(pm_run=long_run, role="challenger")

    assert first.custom_id()[:48] == second.custom_id()[:48]
    assert first.custom_id() != second.custom_id()


def test_the_wire_id_is_a_pure_function_of_the_key() -> None:
    """A plan reloaded from disk must address the same requests it did before."""
    assert _key().custom_id() == _key().custom_id()


def test_turns_of_one_debate_share_a_transcript_identity() -> None:
    """Grouping is by debate, not by turn: the role and round are excluded."""
    defender = _key(role="defender", round=1)
    judge = _key(role="judge", round=JUDGE_ROUND)

    assert defender.debate == judge.debate
    assert defender.debate != _key(repeat=2).debate
