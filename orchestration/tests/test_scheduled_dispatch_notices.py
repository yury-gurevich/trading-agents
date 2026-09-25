"""S219 notification and override tests for the scheduled dispatcher.

Agent: orchestration
Role: prove held runs notify once and accept a human override.
External I/O: none; Telegram is injected.
"""

from __future__ import annotations

from datetime import timedelta
from importlib import import_module

from contracts.provider import RUN_REQUEST_LABEL
from kernel import InMemoryGraphStore
from orchestration.tests.scheduled_dispatch_human_helpers import (
    NOW,
    FakeAnswer,
    FakeTelegram,
    active_hold,
    dispatch,
    preflight,
)


def test_c1_ready_fleet_is_silent_and_unchanged() -> None:
    """C1: a ready fleet places the unchanged run without Telegram activity."""
    graph = InMemoryGraphStore()
    preflight(graph, passed=True)
    graph.merge_node(
        "RunHold",
        "hold:old",
        {"run_id": "old", "as_of": "2026-07-07", "state": "held", "released_at": "x"},
    )
    before = graph.get_node("RunHold", "hold:old")
    telegram = FakeTelegram()

    result = dispatch(graph, telegram)

    assert result.action == "placed"
    assert telegram.polls == 0
    assert telegram.sent == []
    assert graph.list_nodes("RunHoldAnswer") == ()
    assert graph.get_node("RunHold", "hold:old") == before


def test_c2_new_hold_sends_one_notice_and_marks_the_hold() -> None:
    """DSP-OUT-05 / DSP-OBS-01: a newly held run has one notice and evidence."""
    graph = InMemoryGraphStore()
    preflight(graph, passed=False, failures=("unrecoverable:provider:credential",))
    telegram = FakeTelegram()

    result = dispatch(graph, telegram)

    assert result.action == "held"
    assert len(telegram.sent) == 1
    (hold,) = graph.list_nodes("RunHold")
    assert "notified_at" in hold.props
    assert hold.props["notice_message_id"] == 1


def test_c3_notice_has_act_by_and_exactly_two_callback_buttons() -> None:
    """DSP-OUT-05: the notice states action time and both legal answers."""
    module = import_module("orchestration.telegram_client")
    sent: list[tuple[str, dict[str, object], float]] = []

    def sender(method: str, payload: dict[str, object], timeout: float) -> object:
        sent.append((method, payload, timeout))
        return {"ok": True, "result": {"message_id": 41}}

    credential = "test"
    client = module.TelegramClient(api_token=credential, chat_id="chat", sender=sender)

    assert (
        client.send_hold_notice(
            run_id="sched-2026-07-08",
            failures=("unrecoverable:provider:credential",),
            act_by="23:20 UTC",
        )
        == 41
    )
    method, payload, _ = sent[0]
    assert method == "sendMessage"
    assert "23:20 UTC" in str(payload["text"])
    assert payload["reply_markup"] == {
        "inline_keyboard": [
            [
                {"text": "Run now", "callback_data": "run_now:sched-2026-07-08"},
                {
                    "text": "Skip today",
                    "callback_data": "skip_today:sched-2026-07-08",
                },
            ]
        ]
    }


def test_c4_second_fire_on_one_hold_sends_no_second_notice() -> None:
    """DSP-OUT-05: notification is once per active hold, not once per cron fire."""
    graph = InMemoryGraphStore()
    preflight(graph, passed=False)
    telegram = FakeTelegram()

    dispatch(graph, telegram)
    dispatch(graph, telegram)

    assert len(telegram.sent) == 1


def test_c5_rehold_after_release_gets_its_own_notice() -> None:
    """DSP-STA-01: a released hold is untouched and a new hold is announced."""
    graph = InMemoryGraphStore()
    telegram = FakeTelegram()
    preflight(graph, passed=False)
    dispatch(graph, telegram)
    preflight(graph, passed=True, checked_at=NOW - timedelta(minutes=4))
    dispatch(graph, telegram)
    preflight(graph, passed=False, checked_at=NOW - timedelta(minutes=3))

    dispatch(graph, telegram)

    holds = graph.list_nodes("RunHold")
    assert len(holds) == 2
    assert "released_at" in holds[0].props
    assert holds[1].props["notice_message_id"] == 2


def test_c6_run_now_places_despite_a_failing_preflight() -> None:
    """DSP-IN-04 / DSP-OBS-01: an effective run-now answer overrides the hold."""
    graph = InMemoryGraphStore()
    preflight(graph, passed=False)
    active_hold(graph)
    telegram = FakeTelegram(
        answers=(FakeAnswer(10, "run_now", "sched-2026-07-08", "callback-10"),)
    )

    result = dispatch(graph, telegram)

    assert result.action == "placed"
    assert graph.get_node(RUN_REQUEST_LABEL, "run-request:sched-2026-07-08")
    hold = graph.get_node("RunHold", "hold:sched-2026-07-08")
    assert hold is not None
    assert hold.props["answered_with"] == "run_now"


def test_c7_skip_today_writes_no_run_and_formats_operator_skip() -> None:
    """DSP-IN-04 / DSP-OUT-02: skip-today is an operator decision, not an error."""
    graph = InMemoryGraphStore()
    preflight(graph, passed=False)
    active_hold(graph)
    telegram = FakeTelegram(
        answers=(FakeAnswer(11, "skip_today", "sched-2026-07-08", "callback-11"),)
    )

    result = dispatch(graph, telegram)

    formatter = import_module("runpy").run_path("scripts/dispatch_scheduled_run.py")[
        "format_dispatch_result"
    ]
    assert graph.list_nodes(RUN_REQUEST_LABEL) == ()
    hold = graph.get_node("RunHold", "hold:sched-2026-07-08")
    assert hold is not None
    assert hold.props["answered_with"] == "skip_today"
    assert formatter(result) == "skipped sched-2026-07-08 reason=operator"
