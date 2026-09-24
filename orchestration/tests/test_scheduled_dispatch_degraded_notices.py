"""S227 degraded scheduled-dispatch notice tests.

Agent: orchestration
Role: prove degraded runs notify once without operator answer buttons.
External I/O: none; Telegram is injected.
"""

from __future__ import annotations

from importlib import import_module

from contracts.provider import RUN_REQUEST_LABEL
from kernel import InMemoryGraphStore
from orchestration.tests.scheduled_dispatch_human_helpers import (
    FakeTelegram,
    dispatch,
    preflight,
)

_LLM_ONLY_FAILURES = (
    "unrecoverable:deliberator-manager:anthropic:unrecoverable:http_400",
    "unrecoverable:deliberator-opponent:anthropic:unrecoverable:http_400",
    "unrecoverable:deliberator-proponent:anthropic:unrecoverable:http_400",
    "unrecoverable:operator:anthropic:unrecoverable:http_400",
)


def test_degraded_run_sends_one_informational_notice_and_no_hold() -> None:
    """DRIFT-068: degraded placement tells the operator once without answer buttons."""
    graph = InMemoryGraphStore()
    preflight(graph, passed=False, failures=_LLM_ONLY_FAILURES)
    telegram = FakeTelegram()

    first = dispatch(graph, telegram)
    second = dispatch(graph, telegram)

    assert (first.action, second.action) == ("placed", "placed")
    assert telegram.sent == []
    assert len(telegram.degraded_sent) == 1
    assert telegram.degraded_sent[0] == {
        "run_id": "sched-2026-07-08",
        "failures": _LLM_ONLY_FAILURES,
    }
    run = graph.get_node(RUN_REQUEST_LABEL, "run-request:sched-2026-07-08")
    assert run is not None
    assert "degraded_notified_at" in run.props
    assert graph.list_nodes("RunHold") == ()


def test_degraded_notice_missing_message_id_does_not_mark_notified() -> None:
    """DRIFT-068: failed degraded notice evidence does not suppress a retry."""
    graph = InMemoryGraphStore()
    preflight(graph, passed=False, failures=_LLM_ONLY_FAILURES)
    telegram = FakeTelegram(degraded_returns_none=True)

    result = dispatch(graph, telegram)

    assert result.action == "placed"
    assert len(telegram.degraded_sent) == 1
    run = graph.get_node(RUN_REQUEST_LABEL, "run-request:sched-2026-07-08")
    assert run is not None
    assert "degraded_notified_at" not in run.props


def test_degraded_notice_has_no_callback_buttons() -> None:
    """DRIFT-068: degraded notice is informational, not an answer request."""
    module = import_module("orchestration.telegram_client")
    sent: list[tuple[str, dict[str, object], float]] = []

    def sender(method: str, payload: dict[str, object], timeout: float) -> object:
        sent.append((method, payload, timeout))
        return {"ok": True, "result": {"message_id": 42}}

    credential = "test"
    client = module.TelegramClient(api_token=credential, chat_id="chat", sender=sender)

    assert (
        client.send_degraded_notice(
            run_id="sched-2026-07-08",
            failures=("unrecoverable:operator:anthropic:unrecoverable:http_400",),
        )
        == 42
    )
    _, payload, _ = sent[0]
    assert "No new buys tonight" in str(payload["text"])
    assert "reply_markup" not in payload


def test_degraded_notice_records_missing_message_id() -> None:
    """DRIFT-068: a Telegram response without an id is visible to fault_safe."""
    module = import_module("orchestration.telegram_client")

    def sender(_method: str, _payload: dict[str, object], _timeout: float) -> object:
        return {"ok": True, "result": {}}

    credential = "test"
    client = module.TelegramClient(api_token=credential, chat_id="chat", sender=sender)

    assert (
        client.send_degraded_notice(
            run_id="sched-2026-07-08",
            failures=("unrecoverable:operator:anthropic:unrecoverable:http_400",),
        )
        is None
    )
    assert client.last_error == "telegram_message_id_missing"
