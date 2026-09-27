"""Window-edge and unreadable-record tests for the unattended scorecard.

Agent: surfaces
Role: prove what falls outside the window, and that no record is skipped or guessed.
External I/O: none; the graph is in-memory and the verdict function is a counting fake.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time

import pytest

from kernel import InMemoryGraphStore
from surfaces.queries.scorecard import scorecard
from surfaces.queries.scorecard_actions import ScorecardDataError, human_actions
from surfaces.scorecard_settings import ScorecardSettings
from surfaces.tests.scorecard_fixtures import (
    WEEK,
    at,
    command,
    hold_answer,
    manual_run,
    resume,
    score,
    session,
)


def test_actions_outside_the_window_count_on_no_session() -> None:
    """SRF-OUT-08: at the previous session's placement, or after the last, is outside.

    The first counted session is Monday 2026-09-21; its window opens at Friday's
    placement (22:30 UTC, no RunRequest). A hold answer naming a session the
    window does not count is placed by its time, after the last placement.
    """
    graph = InMemoryGraphStore()
    for day in WEEK:
        session(graph, day, verdict="PASS")
    command(graph, at(date(2026, 9, 18), 22, 30), key="opening", family="reject")
    command(graph, at(WEEK[4], 23), key="tonight", family="reject")
    hold_answer(graph, "sched-2026-09-28", at(date(2026, 9, 28), 22, 40))

    card = score(graph, 8)

    assert [dict(row.actions) for row in card.sessions] == [{}] * 5


def test_a_resume_is_one_resume_never_also_a_run() -> None:
    """SRF-OUT-08: a resume child copies its source's `requested_at`; it counts once."""
    graph = InMemoryGraphStore()
    manual_run(graph, "manual-2026-09-22", "2026-09-22")
    resume(graph, "manual-2026-09-22", "pm", at(WEEK[2], 1))

    kinds = sorted(action.kind for action in human_actions(graph, time(22, 30)))

    assert kinds == ["resume", "run"]


@pytest.mark.parametrize("stored", [None, "yesterday", "2026-13-45"])
def test_a_record_with_no_readable_time_is_never_skipped(stored: str | None) -> None:
    """SRF-OUT-08: an action that cannot be placed stops the count, never vanishes."""
    graph = InMemoryGraphStore()
    session(graph, WEEK[4], verdict="PASS")
    graph.merge_node("DeployRecord", "deploy:x", {"deployed_at": stored})

    with pytest.raises(ScorecardDataError, match="one DeployRecord carries no"):
        score(graph, 2)


def test_an_unreadable_placement_is_never_guessed() -> None:
    """SRF-OUT-08: a session whose `requested_at` cannot be read stops the count."""
    graph = InMemoryGraphStore()
    session(graph, WEEK[4], verdict="PASS", requested_at="soon")

    with pytest.raises(ScorecardDataError, match="one RunRequest carries no"):
        score(graph, 2)


def test_an_empty_window_is_unavailable() -> None:
    """SRF-OUT-08: with no session closed in the window there is nothing to score."""
    card = scorecard(
        InMemoryGraphStore(),
        now=datetime(2026, 9, 21, 10, tzinfo=UTC),
        settings=ScorecardSettings(scorecard_window_days=1),
    )

    assert (card.status, card.counted, card.g1, card.g3) == (
        "unavailable",
        0,
        None,
        None,
    )
