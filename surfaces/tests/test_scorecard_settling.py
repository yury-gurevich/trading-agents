"""Planner-review tests for the unattended scorecard: unsettled words and long clocks.

Agent: surfaces
Role: prove a brief's UNPROVEN is re-judged, and a clock can outrun a short window.
External I/O: none; in-memory graph only.

Both were found in S236's handback. The brief is sent before the next open, so every
run that submitted orders is briefed UNPROVEN; kept as final, no trading night would
ever count as complete. And a 30-day window holds 18-23 sessions, so a clock bounded
by it could not reach a 20-session target on 28 days of 2026-27 (DL-235 amendment).
"""

from __future__ import annotations

from datetime import date

from kernel.graph_memory import InMemoryGraphStore
from surfaces.queries.scorecard import scorecard
from surfaces.queries.scorecard_verdicts import VerdictMemo
from surfaces.scorecard_settings import ScorecardSettings
from surfaces.tests.scorecard_fixtures import NOW, WEEK, CountingJudge, session

# Ten sessions ending Friday 2026-09-25; 2026-09-11 before them has no RunRequest.
_TEN = (
    *(date(2026, 9, day) for day in (14, 15, 16, 17, 18)),
    *WEEK,
)


def test_a_briefed_unproven_is_judged_again_by_the_gate() -> None:
    """SRF-OUT-08: a stored UNPROVEN is not final; the gate's settled word counts."""
    graph = InMemoryGraphStore()
    session(graph, WEEK[-1], verdict="UNPROVEN")
    judge = CountingJudge({"sched-2026-09-25": "PASS"})

    card = scorecard(
        graph,
        now=NOW,
        settings=ScorecardSettings(scorecard_window_days=2),
        verdicts=VerdictMemo(judge),
    )

    assert [(row.verdict, row.complete) for row in card.sessions] == [("PASS", True)]
    assert judge.calls == ["sched-2026-09-25"]


def test_an_unsettled_judgement_is_asked_again_and_a_settled_one_never() -> None:
    """SRF-OUT-08: the memo keeps settled words only; UNPROVEN is asked again."""
    graph = InMemoryGraphStore()
    session(graph, WEEK[-1])
    judge = CountingJudge({"sched-2026-09-25": "UNPROVEN"})
    memo = VerdictMemo(judge)
    window = ScorecardSettings(scorecard_window_days=2)

    scorecard(graph, now=NOW, settings=window, verdicts=memo)
    judge.words["sched-2026-09-25"] = "PASS"
    settled = scorecard(graph, now=NOW, settings=window, verdicts=memo)
    scorecard(graph, now=NOW, settings=window, verdicts=memo)

    assert settled.sessions[0].verdict == "PASS"
    assert judge.calls == ["sched-2026-09-25", "sched-2026-09-25"]


def test_a_clock_looks_past_the_window_to_its_target() -> None:
    """SRF-OUT-08: the clocks count back past the window; G1 and G3 stay inside it."""
    graph = InMemoryGraphStore()
    for day in _TEN:
        session(graph, day, verdict="PASS")
    memo = VerdictMemo(CountingJudge({}))

    eight = scorecard(
        graph,
        now=NOW,
        settings=ScorecardSettings(scorecard_window_days=8, scorecard_clock_sessions=8),
        verdicts=memo,
    )
    twenty = scorecard(
        graph,
        now=NOW,
        settings=ScorecardSettings(scorecard_window_days=8),
        verdicts=memo,
    )

    assert (eight.counted, eight.g1) == (5, 1.0)
    assert (eight.unattended, eight.untouched) == (8, 8)
    assert (twenty.counted, twenty.unattended, twenty.untouched) == (5, 10, 10)


def test_a_clock_broken_inside_the_window_reads_no_further() -> None:
    """SRF-OUT-08: the look-back only runs when the whole window holds.

    The sessions before the window are unbriefed and the judge knows none of them, so
    reading them at all would raise.
    """
    graph = InMemoryGraphStore()
    for day in _TEN:
        briefed = day >= WEEK[0]
        word = "FAIL" if day == WEEK[1] else "PASS"
        session(graph, day, verdict=word if briefed else None)
    judge = CountingJudge({})

    card = scorecard(
        graph,
        now=NOW,
        settings=ScorecardSettings(scorecard_window_days=8),
        verdicts=VerdictMemo(judge),
    )

    assert (card.unattended, card.untouched) == (3, 3)
    assert [row.day for row in card.sessions] == list(WEEK)
    assert judge.calls == []
