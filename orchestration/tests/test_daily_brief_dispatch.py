"""S234 daily brief through the scheduled dispatcher's public seam.

Agent: orchestration
Role: prove the brief goes once, after the Snapshot, and never touches placement.
External I/O: none; Telegram is injected.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from kernel import InMemoryGraphStore
from orchestration.tests.daily_brief_fixtures import (
    PREVIOUS_DAY,
    at,
    fire,
    metrics_with,
    performance,
    seed_run,
)
from orchestration.tests.scheduled_dispatch_human_helpers import FakeTelegram, preflight

if TYPE_CHECKING:
    from kernel import Node

_RUN_KEY = "run-request:sched-2026-09-25"
_A1_TEXT = "\n".join(
    (
        "\U0001f7e2 PASS · sched-2026-09-25 · Sat 26 Sep 08:50",
        "Equity $101,976.32 (−$24.40 since sched-2026-09-24)",
        "vs SPY: -0.43 pts over 33 sessions at 21% invested",
        "Orders: none",
        "Filled: none",
        "Needs you: nothing",
    )
)
# Every textual form the two stored figures could take outside the message.
AMOUNTS = ("$", "101,976", "101976", "10197632", "24.40", "10200072", "102,000")


def seed_pair(graph: InMemoryGraphStore, *, briefed: bool = False) -> None:
    """sched-2026-09-24 (briefed, 10,200,072) and sched-2026-09-25 (10,197,632)."""
    seed_run(
        graph,
        PREVIOUS_DAY,
        pm_created="2026-09-24T22:40:00+00:00",
        metrics=metrics_with(performance(10_200_072.0)),
        briefed=True,
    )
    seed_run(graph, pm_created="2026-09-25T22:41:00+00:00", briefed=briefed)
    preflight(graph, passed=True, checked_at=at(22, 45))


def run_request(graph: InMemoryGraphStore) -> Node:
    """Return the fixture day's RunRequest."""
    node = graph.get_node("RunRequest", _RUN_KEY)
    assert node is not None
    return node


def amount_free(fault: Node) -> bool:
    """Whether a Fault's text carries none of the brief's amounts."""
    text = " ".join(
        str(fault.props.get(name))
        for name in ("error_type", "message", "traceback", "context")
    )
    return not any(amount in text for amount in AMOUNTS)


def test_a1_a_finished_run_gets_its_brief() -> None:
    """DSP-OUT-06 / DSP-IDN-04: one brief carries the run's facts, then its marker.

    A run like sched-2026-09-25: PASS, equity 10,197,632 against the previous
    briefed run's 10,200,072, the reporter's clause, no orders, no fills, nothing
    open. The RunRequest records when, which message, and what verdict it carried.
    """
    graph = InMemoryGraphStore()
    seed_pair(graph)
    telegram = FakeTelegram()

    fire(graph, telegram, at(22, 50))

    assert telegram.briefs == [_A1_TEXT]
    run = run_request(graph)
    assert run.props["brief_sent_at"] == "2026-09-25T22:50:00+00:00"
    assert run.props["brief_message_id"] == 101
    assert run.props["brief_verdict"] == "PASS"


def test_a3_nothing_before_the_snapshot_then_red_on_the_last_fire() -> None:
    """DSP-TRG-03: no brief before the Snapshot; one RED brief on the 23:50 fire.

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
    """DSP-FAIL-03 / DSP-STA-02 / DSP-SEC-02: a failed send is only a fault.

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
    assert all(amount_free(fault) for fault in faults)
    assert "brief_sent_at" not in run_request(graph).props

    telegram.brief_returns_none = False
    fire(graph, telegram, at(23, 10))

    assert len(telegram.briefs) == 3
    assert run_request(graph).props["brief_message_id"] == 103
