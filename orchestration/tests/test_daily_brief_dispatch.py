"""S234 daily brief through the scheduled dispatcher's public seam.

Agent: orchestration
Role: prove the brief goes once, after the Snapshot, and never touches placement.
External I/O: none; Telegram is injected.
"""

from __future__ import annotations

from kernel import InMemoryGraphStore
from orchestration.tests.daily_brief_fixtures import at, fire, seed_run
from orchestration.tests.daily_brief_scenarios import (
    A1_TEXT,
    amount_free,
    fault_text,
    run_request,
    seed_pair,
)
from orchestration.tests.scheduled_dispatch_human_helpers import FakeTelegram, preflight


def test_a1_a_finished_run_gets_its_brief() -> None:
    """DSP-OUT-06 / DSP-IDN-04 / DSP-IDM-03: one brief with the facts, then its marker.

    A run like sched-2026-09-25: PASS, equity 10,197,632 against the previous
    briefed run's 10,200,072, the reporter's clause, no orders, no fills, nothing
    open. The RunRequest records when, which message, and what verdict it carried.
    """
    graph = InMemoryGraphStore()
    seed_pair(graph)
    telegram = FakeTelegram()

    fire(graph, telegram, at(22, 50))

    assert telegram.briefs == [A1_TEXT]
    run = run_request(graph)
    assert run.props["brief_sent_at"] == "2026-09-25T22:50:00+00:00"
    assert run.props["brief_message_id"] == 101
    assert run.props["brief_verdict"] == "PASS"


def test_a2_a_second_fire_sends_nothing() -> None:
    """DSP-IDM-03: one brief per run id; the marker silences every later fire.

    The later fires include 23:50, so a briefed run is never re-sent as RED either.
    """
    graph = InMemoryGraphStore()
    seed_pair(graph)
    telegram = FakeTelegram()

    for minute in ((22, 50), (23, 0), (23, 50)):
        fire(graph, telegram, at(*minute))

    assert telegram.briefs == [A1_TEXT]
    assert run_request(graph).props["brief_message_id"] == 101


def test_a3_nothing_before_the_snapshot_then_red_on_the_last_fire() -> None:
    """DSP-TRG-03 / DSP-IDM-03: no brief before the Snapshot; one RED brief at 23:50.

    The run stopped after execution. The 22:40 fire stays silent because the run
    may still finish; the day's last fire names the last stage that finished.
    """
    graph = InMemoryGraphStore()
    seed_run(graph, pm_created="2026-09-25T22:41:00+00:00", through="ExecutionRun")
    preflight(graph, passed=True, checked_at=at(22, 35))
    telegram = FakeTelegram()

    fire(graph, telegram, at(22, 40))
    assert telegram.briefs == []

    fire(graph, telegram, at(23, 50))

    assert telegram.briefs == [
        "\n".join(
            (
                "\U0001f534 NOT FINISHED · sched-2026-09-25 · Sat 26 Sep 09:50",
                "Last stage finished: execution",
                "Orders: none",
                "Needs you: nothing",
            )
        )
    ]
    assert run_request(graph).props["brief_verdict"] == "NOT_FINISHED"


def test_a6_a_failed_send_changes_nothing_else_and_the_next_fire_retries() -> None:
    """DSP-FAIL-03 / DSP-STA-02 / DSP-SEC-02 / DSP-IDM-03: a failed send is a fault.

    The port first raises (quoting the text it failed to send), then answers with
    no message id. Each becomes a Fault that carries no amount, no marker is
    written, and each fire returns exactly what it returns with no brief due. The
    next fire sends.
    """
    no_brief = InMemoryGraphStore()
    seed_pair(no_brief, briefed=True)
    graph = InMemoryGraphStore()
    seed_pair(graph)
    telegram = FakeTelegram(brief_raises=True)

    raised = fire(graph, telegram, at(22, 50))
    telegram.brief_raises, telegram.brief_returns_none = False, True
    unanswered = fire(graph, telegram, at(23, 0))

    assert raised == fire(no_brief, FakeTelegram(), at(22, 50))
    assert unanswered == fire(no_brief, FakeTelegram(), at(23, 0))
    faults = graph.list_nodes("Fault")
    assert len(faults) == 2
    assert all("daily brief" in str(fault.props["message"]) for fault in faults)
    assert all(amount_free(fault_text(fault)) for fault in faults)
    assert "brief_sent_at" not in run_request(graph).props

    telegram.brief_returns_none = False
    fire(graph, telegram, at(23, 10))

    assert len(telegram.briefs) == 3
    assert run_request(graph).props["brief_message_id"] == 103
