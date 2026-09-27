"""G1 and G3 tests for the unattended scorecard.

Agent: surfaces
Role: prove the scorecard counts complete sessions and human actions from graph facts.
External I/O: none; the graph is in-memory and the verdict function is a counting fake.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from typing import get_args

import pytest

from contracts.operator import IntentFamily
from kernel import FakeLLMClient, InMemoryGraphStore
from orchestration.packs.trading_acceptance import TradingAcceptanceResult
from surfaces.context import build_test_context
from surfaces.mcp_tools import dispatch_tool
from surfaces.queries.scorecard import scorecard
from surfaces.queries.scorecard_actions import READING_FAMILIES, human_actions
from surfaces.queries.scorecard_verdicts import VerdictMemo
from surfaces.tests.scorecard_fixtures import (
    NOW,
    WEEK,
    CountingJudge,
    at,
    command,
    escalation,
    hold_answer,
    manual_run,
    resume,
    session,
    settings,
)

_TICK = time(22, 30)


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
    """SRF-OUT-08 / OPR-OUT-06: status and explain intents, and explain calls, read.

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


def test_a4_every_acting_kind_counts() -> None:
    """SRF-OUT-08: each kind of human action makes its healthy session hands-on.

    One healthy session each: an approve, a command that produced no Intent, a run
    started by hand, a resume, a hold answer and an escalation. The hold answer is
    made at 22:40 UTC, after the placing tick, and still counts on the run it names.
    """
    graph = InMemoryGraphStore()
    days = (date(2026, 9, 18), *WEEK)
    for day in days:
        session(graph, day, verdict="PASS")
    command(graph, at(days[0], 5), key="approve", family="approve")
    command(graph, datetime(2026, 9, 19, 12, tzinfo=UTC), key="huh", outcome="refused")
    manual_run(graph, "manual-2026-09-22", "2026-09-22")
    resume(graph, "sched-2026-09-22", "pm", at(days[3], 1))
    hold_answer(graph, "sched-2026-09-24", at(days[4], 22, 40))
    escalation(graph, at(days[5], 4, 16))

    card = scorecard(
        graph,
        now=NOW,
        settings=settings(window_days=9),
        verdicts=VerdictMemo(CountingJudge({})),
    )

    assert [(row.run_id, dict(row.actions)) for row in card.sessions] == [
        ("sched-2026-09-18", {"command": 1}),
        ("sched-2026-09-21", {"command": 1}),
        ("sched-2026-09-22", {"run": 1}),
        ("sched-2026-09-23", {"resume": 1}),
        ("sched-2026-09-24", {"hold_answer": 1}),
        ("sched-2026-09-25", {"escalation": 1}),
    ]
    assert (card.hands_on, card.healthy) == (6, 6)
    assert (card.unattended, card.untouched) == (0, 0)


@pytest.mark.parametrize("family", get_args(IntentFamily))
def test_every_intent_family_but_reading_acts(family: str) -> None:
    """SRF-OUT-08 / OPR-TYP-02: status and explain read; every other family acts.

    Pinned to the contract's literal, so a family the contract adds later acts
    until someone decides otherwise: the safe side for an autonomy claim.
    """
    graph = InMemoryGraphStore()
    command(graph, NOW, key=family, family=family)

    kinds = [action.kind for action in human_actions(graph, _TICK)]

    assert set(get_args(IntentFamily)) >= READING_FAMILIES
    assert kinds == ([] if family in READING_FAMILIES else ["command"])


def test_the_operators_own_reading_records_are_never_actions() -> None:
    """SRF-OUT-08 / OPR-OUT-06 / OPR-OUT-07: the operator's real reading writes count 0.

    "Explain this run" audits with no Intent (OPR-OUT-06); a typed explain command
    writes an explain Intent and then that second, Intent-less audit. A pause is a
    human acting, written by the same operator, and it is the one action counted.
    """
    graph = InMemoryGraphStore()
    pause = '{"family": "pause", "parameters": {}, "outcome": "intent"}'
    ask = '{"family": "explain", "parameters": {"subject": "why"}, "outcome": "intent"}'
    ctx = build_test_context(graph, llm=FakeLLMClient({"pause": pause, "why": ask}))

    dispatch_tool(ctx, "explain", {"subject": "the run", "run_id": "sched-2026-09-25"})
    dispatch_tool(ctx, "command", {"text": "why no trades", "channel": "dashboard"})
    dispatch_tool(ctx, "command", {"text": "pause", "channel": "dashboard"})

    families = sorted(str(node.props["family"]) for node in graph.list_nodes("Intent"))
    audits = len(graph.list_nodes("CommandAudit"))
    kinds = [action.kind for action in human_actions(graph, _TICK)]
    assert (families, audits, kinds) == (["explain", "pause"], 4, ["command"])
