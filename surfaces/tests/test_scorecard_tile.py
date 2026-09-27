"""Dashboard tile tests for the unattended scorecard.

Agent: surfaces
Role: prove the tile's tone and words, its unavailable cases, and the blind-spot list.
External I/O: none; the graph is in-memory and every session is briefed.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

import pytest

from kernel import InMemoryGraphStore
from surfaces.dashboard.projections_scorecard import scorecard_vital
from surfaces.dashboard.settings import DashboardSettings
from surfaces.queries.scorecard_text import NOT_COUNTED
from surfaces.scorecard_settings import ScorecardSettings
from surfaces.tests.scorecard_fixtures import NOW, WEEK, at, command, session, settings

if TYPE_CHECKING:
    from kernel import Node

# A sprint, design-log, drift or law-clause id anywhere in the tile (SRF-OUT-05).
_IDS = re.compile(r"\bS\d{2,3}\b|\bDL-\d+|\bDRIFT-\d+|\b[A-Z]{2,5}-[A-Z]{2,4}-\d{2}\b")


def _strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        return [text for item in value.values() for text in _strings(item)]
    if isinstance(value, list | tuple):
        return [text for item in value for text in _strings(item)]
    return []


def _detail(tile: Mapping[str, object]) -> dict[str, str]:
    return dict(cast("list[tuple[str, str]]", tile["detail"]))


def _week(graph: InMemoryGraphStore, words: tuple[str, ...], hands_on: int) -> None:
    for day, word in zip(WEEK, words, strict=True):
        session(graph, day, verdict=word)
    for index in range(hands_on):
        command(graph, at(WEEK[index], 5), key=f"approve-{index}", family="approve")


@pytest.mark.parametrize(
    ("words", "hands_on", "tone", "text"),
    [
        (
            ("PASS", "PASS", "PASS", "PASS", "FAIL"),
            0,
            "crit",
            "unattended 0, untouched 0 of 20 sessions · cycles 80 % · "
            "hands-on 0 of 4 days",
        ),
        (
            ("PASS",) * 5,
            1,
            "warn",
            "unattended 4, untouched 4 of 20 sessions · cycles 100 % · "
            "hands-on 1 of 5 days",
        ),
        (
            ("PASS",) * 5,
            0,
            "good",
            "unattended 5, untouched 5 of 20 sessions · cycles 100 % · "
            "hands-on 0 of 5 days",
        ),
    ],
)
def test_a10_the_tile_is_red_amber_or_green_in_plain_words(
    words: tuple[str, ...], hands_on: int, tone: str, text: str
) -> None:
    """SRF-OUT-08 / SRF-OUT-05: red below the completion goal, amber at hands-on's.

    Amber is 1 hands-on of 5 healthy: exactly the 20 % line, which counts as met.
    No sprint, design-log, drift or clause id appears anywhere in the payload.
    """
    graph = InMemoryGraphStore()
    _week(graph, words, hands_on)

    tile = scorecard_vital(graph, settings(), now=NOW)

    assert (tile["tone"], tile["text"]) == (tone, text)
    assert [value for value in _strings(tile) if _IDS.search(value)] == []


def test_a10_an_empty_window_reads_unavailable_and_shows_no_number() -> None:
    """SRF-OUT-08: nothing closed in the window is unavailable, never zero."""
    monday_morning = datetime(2026, 9, 21, 10, tzinfo=UTC)

    tile = scorecard_vital(InMemoryGraphStore(), settings(1), now=monday_morning)

    assert tile == {
        "status": "unavailable",
        "tone": "idle",
        "text": "unattended: unavailable",
        "reason": "no scheduled session in the window has closed yet",
    }


class _UnreadableGraph(InMemoryGraphStore):
    def list_nodes(self, label: str) -> tuple[Node, ...]:
        raise RuntimeError(f"postgres://operator:secret@spine/{label} refused")


def test_an_unreadable_graph_degrades_the_tile_and_leaks_nothing() -> None:
    """SRF-OUT-08 / SRF-FAIL-01 / SRF-SEC-02: unavailable in plain words, no raw error.

    The tile stays a normal payload, and the store's error text never reaches it.
    """
    tile = scorecard_vital(_UnreadableGraph(), settings(), now=NOW)

    assert (tile["tone"], tile["reason"]) == ("idle", "the graph could not be read")
    assert "secret" not in str(tile)


def test_a_record_with_no_readable_time_is_named_not_guessed() -> None:
    """SRF-OUT-08: the tile says which kind of record it cannot place, and no number."""
    graph = InMemoryGraphStore()
    _week(graph, ("PASS",) * 5, 0)
    graph.merge_node("Escalation", "escalation:x", {"created_at": "yesterday"})

    tile = scorecard_vital(graph, settings(), now=NOW)

    assert (tile["status"], tile["reason"]) == (
        "unavailable",
        "one Escalation carries no readable time",
    )


def test_with_no_healthy_session_there_is_no_hands_on_share() -> None:
    """SRF-OUT-08: G3 has no denominator, so it is said, never shown as 0 %."""
    graph = InMemoryGraphStore()
    _week(graph, ("FAIL",) * 5, 0)

    tile = scorecard_vital(graph, settings(), now=NOW)

    assert tile["tone"] == "crit"
    assert _detail(tile)["Hands-on days"] == "no healthy session to judge"
    assert "no session was healthy, so there is no hands-on share" in str(
        tile["summary"]
    )


def test_a12_every_answer_names_what_the_graph_cannot_see() -> None:
    """SRF-OUT-08: broker actions, Azure changes but deploys, script repairs: named."""
    graph = InMemoryGraphStore()
    _week(graph, ("PASS",) * 5, 0)

    tile = scorecard_vital(graph, settings(), now=NOW)

    assert tile["not_counted"] == [
        "broker orders placed or cancelled by hand",
        "Azure changes other than a recorded deploy",
        "graph repairs made by scripts",
    ]
    assert all(blind in str(tile["summary"]) for blind in NOT_COUNTED)


def test_the_tile_lists_sessions_newest_first_with_their_actions() -> None:
    """SRF-OUT-08: per-session rows carry the date, the gate's word and the kinds."""
    graph = InMemoryGraphStore()
    _week(graph, ("NO_TRADE", "PASS", "PASS", "PASS", "NOT_FINISHED"), 1)

    tile = scorecard_vital(graph, settings(), now=NOW)

    assert tile["sessions"] == [
        ["2026-09-25 NOT FINISHED", "no human action"],
        ["2026-09-24 PASS", "no human action"],
        ["2026-09-23 PASS", "no human action"],
        ["2026-09-22 PASS", "no human action"],
        ["2026-09-21 NO TRADE", "1 command"],
    ]
    assert _detail(tile)["Window"] == "5 sessions, 2026-09-21 to 2026-09-25"


def test_the_four_goals_are_the_prds_and_the_dashboard_inherits_them() -> None:
    """SRF-OUT-08: 30 days, 95 %, 20 %, 20 sessions: one declaration, tile and tool."""
    goals = ScorecardSettings()

    assert (
        goals.scorecard_window_days,
        goals.scorecard_g1_target,
        goals.scorecard_g3_target,
        goals.scorecard_clock_sessions,
        goals.dispatcher_fire_utc,
    ) == (30, 0.95, 0.20, 20, "22:30")
    assert issubclass(DashboardSettings, ScorecardSettings)
    assert set(ScorecardSettings.model_fields) <= set(DashboardSettings.model_fields)
