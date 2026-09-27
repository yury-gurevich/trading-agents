"""Attribution, clock and window tests for the unattended scorecard.

Agent: surfaces
Role: prove each human action lands on the run it preceded, and the clocks count back.
External I/O: none; the graph is in-memory and the verdict function is a counting fake.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from kernel import InMemoryGraphStore
from surfaces.queries.scorecard import scorecard
from surfaces.queries.scorecard_verdicts import VerdictMemo
from surfaces.tests.scorecard_fixtures import (
    CountingJudge,
    command,
    session,
    settings,
)

_TUESDAY = datetime(2026, 9, 29, 3, 0, tzinfo=UTC)


def test_a6_a_weekend_action_belongs_to_mondays_run() -> None:
    """SRF-OUT-08: an action belongs to the first counted session placed after it.

    Friday's and Monday's runs are placed at 22:30 UTC; an approve at Saturday
    03:00 UTC falls between them, so it counts against Monday's run, not Friday's.
    """
    graph = InMemoryGraphStore()
    session(graph, date(2026, 9, 25), verdict="PASS", requested_at="2026-09-25T22:30:00")
    session(graph, date(2026, 9, 28), verdict="PASS", requested_at="2026-09-28T22:30:00")
    command(graph, datetime(2026, 9, 26, 3, 0, tzinfo=UTC), key="sat", family="approve")

    card = scorecard(
        graph,
        now=_TUESDAY,
        settings=settings(window_days=4),
        verdicts=VerdictMemo(CountingJudge({})),
    )

    assert [(row.run_id, dict(row.actions)) for row in card.sessions] == [
        ("sched-2026-09-25", {}),
        ("sched-2026-09-28", {"command": 1}),
    ]
