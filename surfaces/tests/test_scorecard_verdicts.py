"""Verdict-source tests for the unattended scorecard.

Agent: surfaces
Role: prove each session's word is the acceptance gate's, stored or judged only once.
External I/O: none; the graph is in-memory, Telegram and the verdict function are fakes.
"""

from __future__ import annotations

import inspect
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, cast

import pytest

from kernel import InMemoryGraphStore
from orchestration.packs.trading_acceptance import accept_run
from orchestration.tests.daily_brief_fixtures import at as fire_at
from orchestration.tests.daily_brief_fixtures import fire
from orchestration.tests.daily_brief_scenarios import run_request, seed_pair
from orchestration.tests.scheduled_dispatch_human_helpers import FakeTelegram
from surfaces import scorecard_tool as tool_module
from surfaces.context import SurfaceContext
from surfaces.dashboard.projections_scorecard import scorecard_vital
from surfaces.queries import scorecard as scorecard_module
from surfaces.queries.scorecard import scorecard
from surfaces.queries.scorecard_verdicts import PROCESS_VERDICTS, VerdictMemo
from surfaces.scorecard_settings import ScorecardSettings
from surfaces.tests.scorecard_fixtures import (
    NOW,
    WEEK,
    CountingJudge,
    session,
    settings,
)

if TYPE_CHECKING:
    from kernel import MessageBus


def test_a2_production_judges_with_accept_run_itself() -> None:
    """SRF-OUT-08: the only judge production names is `accept_run`, by identity."""
    default = inspect.signature(VerdictMemo).parameters["judge"].default

    assert default is accept_run
    assert PROCESS_VERDICTS.judge is accept_run
    assert vars(scorecard_module)["PROCESS_VERDICTS"] is PROCESS_VERDICTS


def test_a2_the_tile_and_the_tool_share_the_process_memo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SRF-OUT-08: neither names a memo, so both read the process one: one judgement."""
    graph = InMemoryGraphStore()
    session(graph, WEEK[-1])
    judge = CountingJudge({"sched-2026-09-25": "PASS"})
    monkeypatch.setattr(scorecard_module, "PROCESS_VERDICTS", VerdictMemo(judge))
    monkeypatch.setattr(tool_module, "utc_now", lambda: NOW)
    ctx = SurfaceContext(graph, cast("MessageBus", object()))

    tile = scorecard_vital(graph, ScorecardSettings(), now=NOW)
    answer = tool_module.scorecard_tool(ctx, {})

    assert judge.calls == ["sched-2026-09-25"]
    assert tile["summary"] == answer["summary"]


def test_a2_a_stored_brief_verdict_is_used_as_written() -> None:
    """SRF-OUT-08 / DSP-IDM-03: the word the dispatcher's own brief wrote is read as is.

    The brief goes through the dispatcher's public seam, so a renamed property
    would fail here; `accept_run` is never asked about a briefed run.
    """
    graph = InMemoryGraphStore()
    seed_pair(graph)
    fire(graph, FakeTelegram(), fire_at(22, 50))
    judge = CountingJudge({})

    card = scorecard(
        graph,
        now=datetime(2026, 9, 26, 0, 0, tzinfo=UTC),
        settings=settings(window_days=2),
        verdicts=VerdictMemo(judge),
    )

    stored = run_request(graph).props["brief_verdict"]
    assert [(row.run_id, row.verdict) for row in card.sessions] == [
        ("sched-2026-09-24", "PASS"),
        ("sched-2026-09-25", stored),
    ]
    assert judge.calls == []


def test_a5_no_run_is_judged_twice() -> None:
    """SRF-OUT-08: two reads judge each unbriefed run once, and briefed runs never."""
    graph = InMemoryGraphStore()
    words = ("PASS", None, None, "NO_TRADE", None)
    for day, word in zip(WEEK, words, strict=True):
        session(graph, day, verdict=word)
    judge = CountingJudge(
        {
            "sched-2026-09-22": "PASS",
            "sched-2026-09-23": "UNPROVEN",
            "sched-2026-09-25": "FAIL",
        }
    )
    memo = VerdictMemo(judge)

    first = scorecard(graph, now=NOW, settings=settings(), verdicts=memo)
    second = scorecard(graph, now=NOW, settings=settings(), verdicts=memo)

    assert judge.calls == ["sched-2026-09-22", "sched-2026-09-23", "sched-2026-09-25"]
    assert first.sessions == second.sessions


def test_an_empty_stored_word_falls_back_to_the_gate() -> None:
    """SRF-OUT-08: only a stored word is used as written; an empty one is no word."""
    graph = InMemoryGraphStore()
    session(graph, WEEK[-1], verdict="")
    judge = CountingJudge({"sched-2026-09-25": "NO_TRADE"})

    card = scorecard(
        graph, now=NOW, settings=settings(window_days=2), verdicts=VerdictMemo(judge)
    )

    assert [row.verdict for row in card.sessions] == ["NO_TRADE"]
    assert judge.calls == ["sched-2026-09-25"]


def test_a_judge_that_raises_is_asked_again() -> None:
    """SRF-OUT-08: a failed judgement is not remembered as a word; the next read asks.

    The judge is asked on every read until it answers.
    """
    graph = InMemoryGraphStore()
    session(graph, WEEK[-1])
    judge = CountingJudge({})  # no word planted, so judging raises
    memo = VerdictMemo(judge)

    for _ in range(2):
        with pytest.raises(KeyError):
            scorecard(graph, now=NOW, settings=settings(window_days=2), verdicts=memo)

    assert judge.calls == ["sched-2026-09-25", "sched-2026-09-25"]


def test_the_default_window_is_row_nines_twenty_sessions() -> None:
    """SRF-OUT-08: from 2026-09-27 the 30-day window is 2026-08-28 to 2026-09-25."""
    graph = InMemoryGraphStore()

    card = scorecard(
        graph, now=NOW, settings=ScorecardSettings(), verdicts=VerdictMemo()
    )

    assert card.counted == 20
    assert (card.sessions[0].day, card.sessions[-1].day) == (
        date(2026, 8, 28),
        date(2026, 9, 25),
    )
    assert {row.verdict for row in card.sessions} == {"MISSED"}
