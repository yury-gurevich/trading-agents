"""Attribution, clock and window tests for the unattended scorecard.

Agent: surfaces
Role: prove each human action lands on the run it preceded, and the clocks count back.
External I/O: none; the graph is in-memory and the verdict function is a counting fake.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone

from kernel import InMemoryGraphStore
from surfaces.tests.scorecard_fixtures import (
    WEEK,
    at,
    command,
    deploy,
    escalation,
    manual_run,
    score,
    session,
)

_TUESDAY = datetime(2026, 9, 29, 3, 0, tzinfo=UTC)


def test_a6_a_weekend_action_belongs_to_mondays_run() -> None:
    """SRF-OUT-08: an action belongs to the first counted session placed after it.

    Friday's and Monday's runs are placed at 22:30 UTC; an approve at Saturday
    03:00 UTC falls between them, so it counts against Monday's run, not Friday's.
    """
    graph = InMemoryGraphStore()
    session(
        graph, date(2026, 9, 25), verdict="PASS", requested_at="2026-09-25T22:30:00"
    )
    session(
        graph, date(2026, 9, 28), verdict="PASS", requested_at="2026-09-28T22:30:00"
    )
    command(graph, datetime(2026, 9, 26, 3, 0, tzinfo=UTC), key="sat", family="approve")

    card = score(graph, 4, _TUESDAY)

    assert [(row.run_id, dict(row.actions)) for row in card.sessions] == [
        ("sched-2026-09-25", {}),
        ("sched-2026-09-28", {"command": 1}),
    ]


def test_a6_a_bare_date_is_placed_at_the_placing_tick() -> None:
    """SRF-OUT-08: a `requested_at` with no time reads as 22:30 UTC on its date.

    Every writer stores a bare date, and the operator decided it reads at the tick:
    a command at Friday 21:00 UTC precedes Friday's run and counts on it, one at
    23:00 counts on Monday's, and a run started by hand on Friday is Friday's.
    """
    graph = InMemoryGraphStore()
    session(graph, date(2026, 9, 25), verdict="PASS")
    session(graph, date(2026, 9, 28), verdict="PASS")
    command(graph, datetime(2026, 9, 25, 21, tzinfo=UTC), key="before", family="mode")
    command(graph, datetime(2026, 9, 25, 23, tzinfo=UTC), key="after", family="mode")
    manual_run(graph, "manual-2026-09-25", "2026-09-25")

    card = score(graph, 4, _TUESDAY)

    assert [dict(row.actions) for row in card.sessions] == [
        {"command": 1, "run": 1},
        {"command": 1},
    ]


def test_a7_naive_timestamps_read_as_utc() -> None:
    """SRF-OUT-08: a naive `requested_at` beside aware times raises nothing, and places.

    The commands carry a +10:00 offset: 08:00 and 09:00 on 2026-09-25 there are
    22:00 and 23:00 UTC on 2026-09-24, either side of that night's placement.
    """
    graph = InMemoryGraphStore()
    session(graph, WEEK[3], verdict="PASS", requested_at="2026-09-24T22:30:00")
    session(graph, WEEK[4], verdict="PASS", requested_at="2026-09-25T22:30:00")
    zone = timezone(timedelta(hours=10))
    command(graph, datetime(2026, 9, 25, 8, tzinfo=zone), key="early", family="stage")
    command(graph, datetime(2026, 9, 25, 9, tzinfo=zone), key="late", family="stage")

    card = score(graph, 3)

    assert [dict(row.actions) for row in card.sessions] == [
        {"command": 1},
        {"command": 1},
    ]


def test_a8_a_deploy_stops_one_clock_and_an_escalation_both() -> None:
    """SRF-OUT-08: counted back from the latest: untouched 1, unattended 2.

    Latest three sessions: complete and untouched; complete with a deploy;
    complete with an escalation, where both clocks stop.
    """
    graph = InMemoryGraphStore()
    for day in WEEK[2:]:
        session(graph, day, verdict="PASS")
    escalation(graph, at(WEEK[2], 5))
    deploy(graph, at(WEEK[3], 4, 16))

    card = score(graph, 4)

    assert [dict(row.actions) for row in card.sessions] == [
        {"escalation": 1},
        {"deploy": 1},
        {},
    ]
    assert (card.untouched, card.unattended) == (1, 2)
    assert (card.hands_on, card.hands_on_with_deploys, card.healthy) == (1, 2, 3)


def test_a9_open_and_old_sessions_are_not_counted() -> None:
    """SRF-OUT-08: a session before 23:50 UTC on its date, or 31 days back, is out."""
    graph = InMemoryGraphStore()
    for day in (date(2026, 8, 25), date(2026, 8, 26), WEEK[4]):
        session(graph, day, verdict="PASS")
    open_window = datetime(2026, 9, 25, 23, 49, tzinfo=UTC)

    early = score(graph, 30, open_window)
    closed = score(graph, 30, open_window + timedelta(minutes=1))

    assert (early.sessions[0].day, early.sessions[-1].day) == (
        date(2026, 8, 26),
        date(2026, 9, 24),
    )
    assert closed.sessions[-1].day == WEEK[4]
