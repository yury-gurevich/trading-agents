"""S219 Telegram polling and answer-precedence tests.

Agent: orchestration
Role: prove replay-safe, fault-tolerant answer ingestion.
External I/O: none; Telegram is injected.
"""

from __future__ import annotations

from datetime import timedelta
from importlib import import_module

from contracts.provider import RUN_REQUEST_LABEL
from kernel import InMemoryGraphStore
from orchestration.tests.scheduled_dispatch_human_helpers import (
    AS_OF,
    NOW,
    FakeAnswer,
    FakeTelegram,
    active_hold,
    dispatch,
    preflight,
)


def test_c8_same_telegram_update_is_written_once() -> None:
    """C8: replayed Telegram updates do not duplicate RunHoldAnswer evidence."""
    graph = InMemoryGraphStore()
    preflight(graph, passed=False)
    active_hold(graph)
    answer = FakeAnswer(12, "skip_today", "sched-2026-07-08", "callback-12")
    telegram = FakeTelegram(answers=(answer,))

    dispatch(graph, telegram)
    dispatch(graph, telegram)

    assert len(graph.list_nodes("RunHoldAnswer")) == 1


def test_c9_first_answer_wins_when_later_answer_disagrees() -> None:
    """C9: later answer facts remain visible but cannot reverse the first answer."""
    graph = InMemoryGraphStore()
    preflight(graph, passed=False)
    active_hold(graph)
    graph.merge_node(
        "RunHoldAnswer",
        "answer:sched-2026-07-08:telegram:1",
        {
            "run_id": "sched-2026-07-08",
            "as_of": AS_OF.isoformat(),
            "answer": "skip_today",
            "source": "telegram",
            "answered_at": NOW.isoformat(),
            "update_id": 13,
        },
    )
    graph.merge_node(
        "RunHoldAnswer",
        "answer:sched-2026-07-08:dashboard:1",
        {
            "run_id": "sched-2026-07-08",
            "as_of": AS_OF.isoformat(),
            "answer": "run_now",
            "source": "dashboard",
            "answered_at": (NOW + timedelta(minutes=1)).isoformat(),
            "update_id": 0,
        },
    )

    result = dispatch(graph, FakeTelegram())

    assert result.action == "skipped"
    assert graph.list_nodes(RUN_REQUEST_LABEL) == ()
    assert len(graph.list_nodes("RunHoldAnswer")) == 2


def test_c10_every_handled_button_is_acknowledged() -> None:
    """C10: handled callback buttons stop spinning in the Telegram client."""
    graph = InMemoryGraphStore()
    preflight(graph, passed=False)
    active_hold(graph)
    telegram = FakeTelegram(
        answers=(FakeAnswer(14, "skip_today", "sched-2026-07-08", "callback-14"),)
    )

    dispatch(graph, telegram)

    assert telegram.acknowledgements == [("callback-14", "Answer recorded")]


def test_c11_handled_updates_are_confirmed_through_telegram_offset() -> None:
    """C11: the maximum handled update is confirmed with Telegram's cursor."""
    graph = InMemoryGraphStore()
    preflight(graph, passed=False)
    active_hold(graph)
    telegram = FakeTelegram(
        answers=(
            FakeAnswer(15, "skip_today", "sched-2026-07-08", "callback-15"),
            FakeAnswer(18, "run_now", "other-run", "callback-18"),
        )
    )

    dispatch(graph, telegram)

    assert telegram.confirmations == [18]
    calls: list[dict[str, object]] = []

    def sender(_method: str, payload: dict[str, object], _timeout: float) -> object:
        calls.append(payload)
        return {"ok": True, "result": []}

    credential = "test"
    client = import_module("orchestration.telegram_client").TelegramClient(
        api_token=credential, chat_id="chat", sender=sender
    )
    assert client.confirm(up_to_update_id=18) is True
    assert calls == [{"offset": 19}]


def test_c12_telegram_outage_records_a_fault_without_stopping_dispatch() -> None:
    """C12: Telegram failure degrades to a held run and durable fault evidence."""
    graph = InMemoryGraphStore()
    preflight(graph, passed=False)

    result = dispatch(graph, FakeTelegram(fails=True))

    assert result.action == "held"
    assert graph.list_nodes("Fault")


def test_c13_plain_text_updates_are_ignored() -> None:
    """C13: free-text Telegram messages cannot become operator run decisions."""
    module = import_module("orchestration.telegram_client")

    def sender(_method: str, _payload: dict[str, object], _timeout: float) -> object:
        return {"ok": True, "result": [{"update_id": 19, "message": {"text": "run"}}]}

    credential = "test"
    client = module.TelegramClient(api_token=credential, chat_id="chat", sender=sender)

    assert client.poll_answers() == ()


def test_c14_yesterdays_answer_is_inert_for_todays_run() -> None:
    """C14: an answer for another run id cannot decide today's placement."""
    graph = InMemoryGraphStore()
    preflight(graph, passed=False)
    active_hold(graph)
    telegram = FakeTelegram(
        answers=(FakeAnswer(20, "run_now", "sched-2026-07-07", "callback-20"),)
    )

    result = dispatch(graph, telegram)

    assert result.action == "held"
    assert graph.list_nodes(RUN_REQUEST_LABEL) == ()
    (answer,) = graph.list_nodes("RunHoldAnswer")
    assert answer.props["as_of"] == "2026-07-07"


def test_c15_calendar_skip_stays_silent_when_the_fleet_is_failing() -> None:
    """C15: a non-session day is skipped before Telegram or readiness handling."""
    graph = InMemoryGraphStore()
    preflight(graph, passed=False)
    telegram = FakeTelegram()

    result = dispatch(graph, telegram, as_of=AS_OF.replace(day=4))

    assert result.action == "skipped"
    assert telegram.polls == 0
    assert telegram.sent == []
    assert graph.list_nodes("RunHold") == ()


def test_late_run_now_is_recorded_but_never_placed() -> None:
    """DL-183: a late answer remains evidence but cannot start an unsafe run."""
    graph = InMemoryGraphStore()
    preflight(graph, passed=False)
    active_hold(graph)
    telegram = FakeTelegram(
        answers=(FakeAnswer(21, "run_now", "sched-2026-07-08", "callback-21"),)
    )
    controller = import_module("orchestration.scheduled_dispatch_human")

    result = controller.dispatch_with_human_answer(
        graph,
        as_of=AS_OF,
        now=NOW.replace(hour=23, minute=30),
        telegram=telegram,
        universe_source=import_module("agents.scanner.universe").FakeUniverse(
            {"sp500": ("AAPL",)}
        ),
    )

    assert result.action == "held"
    assert graph.list_nodes(RUN_REQUEST_LABEL) == ()
    hold = graph.get_node("RunHold", "hold:sched-2026-07-08")
    assert hold is not None
    assert hold.props["answered_with"] == "run_now"
