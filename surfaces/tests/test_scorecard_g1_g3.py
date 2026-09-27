"""G1 and G3 tests for the unattended scorecard.

Agent: surfaces
Role: prove the scorecard counts complete sessions and human actions from graph facts only.
External I/O: none; the graph is in-memory and the verdict function is a counting fake.
"""

from __future__ import annotations

from datetime import date

import pytest

from kernel import InMemoryGraphStore
from orchestration.packs.trading_acceptance import TradingAcceptanceResult
from surfaces.queries.scorecard import scorecard
from surfaces.queries.scorecard_verdicts import VerdictMemo
from surfaces.tests.scorecard_fixtures import (
    NOW,
    WEEK,
    CountingJudge,
    at,
    command,
    session,
    settings,
)


def test_a1_g1_counts_only_complete_sessions() -> None:
    """SRF-OUT-08: G1 is complete over counted sessions; complete is PASS or NO_TRADE.

    Six sessions carry every word a session can read: the two complete words,
    UNPROVEN (whose `.passed` is true, the trap), FAIL, the brief's NOT_FINISHED,
    and a session with no RunRequest at all, which reads MISSED.
    """
    graph = InMemoryGraphStore()
    judge = CountingJudge(
        {
            "sched-2026-09-18": "PASS",
            "sched-2026-09-22": "UNPROVEN",
            "sched-2026-09-23": "FAIL",
        }
    )
    session(graph, date(2026, 9, 18))
    session(graph, date(2026, 9, 21), verdict="NO_TRADE")
    session(graph, date(2026, 9, 22))
    session(graph, date(2026, 9, 23))
    session(graph, date(2026, 9, 24), verdict="NOT_FINISHED")
    # 2026-09-25 never had a RunRequest.

    card = scorecard(
        graph, now=NOW, settings=settings(window_days=9), verdicts=VerdictMemo(judge)
    )

    assert TradingAcceptanceResult("UNPROVEN", ()).passed
    assert [(row.run_id, row.verdict, row.complete) for row in card.sessions] == [
        ("sched-2026-09-18", "PASS", True),
        ("sched-2026-09-21", "NO_TRADE", True),
        ("sched-2026-09-22", "UNPROVEN", False),
        ("sched-2026-09-23", "FAIL", False),
        ("sched-2026-09-24", "NOT_FINISHED", False),
        ("sched-2026-09-25", "MISSED", False),
    ]
    assert (card.complete, card.counted) == (2, 6)
    assert card.g1 == pytest.approx(2 / 6)


def test_a3_reading_is_never_an_intervention() -> None:
    """SRF-OUT-08 / OPR-OUT-06: status and explain intents, and explain calls, are reading.

    The operator writes a CommandAudit for every explain call and no Intent
    (OPR-OUT-06), so "no Intent" alone cannot mean a human tried to act. The
    middle session's window opens at 2026-09-22 22:30 UTC, the prior placement.
    """
    graph = InMemoryGraphStore()
    for day in WEEK:
        session(graph, day, verdict="PASS")
    middle = WEEK[2]
    command(graph, at(middle, 5), key="status", family="status")
    command(graph, at(middle, 6), key="explain", family="explain")
    command(graph, at(middle, 7), key="explain-call", outcome="explain")

    card = scorecard(
        graph, now=NOW, settings=settings(), verdicts=VerdictMemo(CountingJudge({}))
    )

    row = card.sessions[2]
    assert (row.run_id, dict(row.actions)) == ("sched-2026-09-23", {})
    assert (card.hands_on, card.healthy) == (0, 5)
    assert (card.unattended, card.untouched) == (5, 5)
