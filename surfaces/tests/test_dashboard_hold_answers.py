"""S219 dashboard controls and graph-backed hold-answer tests.

Agent: surfaces
Role: prove the dashboard shows only wired active-hold decisions.
External I/O: none; WSGI and graph are in-memory.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from importlib import import_module

from agents.scanner.universe import FakeUniverse
from contracts.provider import RUN_REQUEST_LABEL
from kernel import InMemoryGraphStore
from orchestration.tests.scheduled_dispatch_human_helpers import FakeTelegram, preflight
from surfaces.dashboard import build_app
from surfaces.tests.test_dashboard_app import invoke

_NOW = datetime(2026, 9, 20, 22, 30, tzinfo=UTC)
_RUN_ID = "sched-2026-07-08"


def _hold(graph: InMemoryGraphStore, *, released: bool = False) -> None:
    props: dict[str, object] = {
        "run_id": _RUN_ID,
        "as_of": "2026-07-08",
        "held_at": _NOW.isoformat(),
        "state": "held",
        "readiness_state": "failing",
        "preflight_key": "preflight:test",
        "failures": ["unrecoverable:provider:credential"],
    }
    if released:
        props["released_at"] = _NOW.isoformat()
    graph.merge_node("RunHold", f"hold:{_RUN_ID}", props)


def test_c16_dashboard_actions_exist_only_for_an_unanswered_active_hold() -> None:
    """C16: dashboard controls are absent without a live unanswered hold."""
    module = import_module("surfaces.dashboard.hold_answer_panel")
    empty = InMemoryGraphStore()
    active = InMemoryGraphStore()
    answered = InMemoryGraphStore()
    released = InMemoryGraphStore()
    _hold(active)
    _hold(answered)
    _hold(released, released=True)
    answered.merge_node(
        "RunHoldAnswer",
        f"answer:{_RUN_ID}:dashboard:1",
        {"run_id": _RUN_ID, "answer": "run_now", "source": "dashboard"},
    )

    assert module.hold_answer_panel(empty) is None
    assert module.hold_answer_panel(released) is None
    assert module.hold_answer_panel(answered) is None
    assert module.hold_answer_panel(active) == {
        "run_id": _RUN_ID,
        "actions": [
            {"answer": "run_now", "label": "Run now"},
            {"answer": "skip_today", "label": "Skip today"},
        ],
    }


def test_c17_dashboard_post_writes_the_shared_fact_and_dispatcher_honours_it() -> None:
    """C17: dashboard and Telegram use the same answer fact and outcome path."""
    graph = InMemoryGraphStore()
    _hold(graph)
    preflight(graph, passed=False)
    app = build_app(graph, now=_NOW)
    body = json.dumps({"run_id": _RUN_ID, "answer": "run_now"}).encode()

    status, _, payload = invoke(app, "/api/hold/answer", "POST", body)

    assert status == "200 OK"
    assert json.loads(payload)["answer"] == "run_now"
    (answer,) = graph.list_nodes("RunHoldAnswer")
    assert answer.props["source"] == "dashboard"
    assert answer.props["update_id"] == 0
    controller = import_module("orchestration.scheduled_dispatch_human")
    result = controller.dispatch_with_human_answer(
        graph,
        as_of=_NOW.date().replace(month=7, day=8),
        now=_NOW,
        telegram=FakeTelegram(),
        universe_source=FakeUniverse({"sp500": ("AAPL",)}),
    )
    assert result.action == "placed"
    assert graph.get_node(RUN_REQUEST_LABEL, "run-request:sched-2026-07-08")


def test_c18_operator_message_and_dashboard_labels_contain_no_internal_ids() -> None:
    """C18: human-facing S219 wording never leaks sprint or law identifiers."""
    client_module = import_module("orchestration.telegram_client")
    panel_module = import_module("surfaces.dashboard.hold_answer_panel")
    sent: list[dict[str, object]] = []

    def sender(_method: str, payload: dict[str, object], _timeout: float) -> object:
        sent.append(payload)
        return {"ok": True, "result": {"message_id": 1}}

    credential = "test"
    client = client_module.TelegramClient(
        api_token=credential, chat_id="chat", sender=sender
    )
    client.send_hold_notice(
        run_id=_RUN_ID,
        failures=("unrecoverable:provider:credential",),
        act_by="23:20 UTC",
    )
    graph = InMemoryGraphStore()
    _hold(graph)
    labels = [
        str(action["label"])
        for action in panel_module.hold_answer_panel(graph)["actions"]
    ]
    rendered = " ".join([str(sent[0]["text"]), *labels])

    assert re.search(r"S\d{3}|DL-\d+|DRIFT-|MST-", rendered) is None
