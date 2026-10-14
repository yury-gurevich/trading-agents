"""A21 edge cases: every kind's words and conservative malformed facts.

Agent: orchestration
Role: prove alarm and brief wording without deriving expectations from production.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from orchestration.container_alarm_text import (
    AlarmGroup,
    brief_summary,
    group_events,
    kind_words,
)
from orchestration.tests.container_sensor_helpers import NOW, fact


@pytest.mark.parametrize(
    ("kind", "code", "words"),
    [
        ("start-failed", None, "failed to start"),
        ("provision-failed", None, "revision failed to provision"),
        ("scaler-failed", None, "scale rule refused"),
        ("memory-kill", None, "killed for memory"),
        ("killed", 137, "killed (exit code 137)"),
        ("platform-error", None, "platform error"),
        ("preempted", None, "moved off its node by the platform"),
        ("exit-error", 1, "exited with code 1"),
        ("exit-error", None, "exited with an error"),
        ("novel", None, "novel"),
    ],
)
def test_a21_every_kind_has_its_words(kind: str, code: int | None, words: str) -> None:
    """DSP-OUT-07: every platform kind uses its prescribed operator-facing words."""
    assert kind_words(AlarmGroup(kind, code, ("provider",), 1, NOW, "")) == words


@pytest.mark.parametrize(
    ("code", "times"), [(None, None), (True, True), ("1", 0), (1.0, -1)]
)
def test_text_reads_malformed_facts_conservatively(code: object, times: object) -> None:
    """DSP-OUT-07: invalid codes, counts and instants never invent evidence."""
    (group,) = group_events(
        [fact("exit-error", exit_code=code, times=times, occurred_at="bad")]
    )
    assert (group.exit_code, group.times, group.last) == (
        None,
        1,
        datetime(1970, 1, 1, tzinfo=UTC),
    )


def test_brief_names_three_kinds_and_counts_the_rest() -> None:
    """DSP-OUT-08: a brief names only three kinds with their apps and counts the
    rest.
    """
    groups = [
        AlarmGroup(kind, None, ("provider",), 1, NOW, "")
        for kind in (
            "start-failed",
            "memory-kill",
            "scaler-failed",
            "platform-error",
            "provision-failed",
        )
    ]
    assert (
        brief_summary(groups)
        == "failed to start (provider); killed for memory (provider); "
        "scale rule refused (provider); and 2 more"
    )
