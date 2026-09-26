"""The bot credential stays inside the Telegram port on every path a fire can take.

Agent: tooling
Role: drive the job entrypoint through each port operation with the real client.
External I/O: none; the graph, clock and HTTPS transport are replaced in-process.
"""

from __future__ import annotations

import inspect
from datetime import datetime, tzinfo
from typing import TYPE_CHECKING

import scripts.dispatch_scheduled_run as entrypoint

from kernel import InMemoryGraphStore
from orchestration.scheduled_dispatch_human import dispatch_with_human_answer
from orchestration.tests.daily_brief_fixtures import at
from orchestration.tests.daily_brief_scenarios import seed_pair
from orchestration.tests.scheduled_dispatch_human_helpers import preflight

if TYPE_CHECKING:
    import pytest

_SENTINEL = "sentinel-bot-credential-for-tests"
_CALLBACK = {
    "update_id": 5,
    "callback_query": {"id": "cb-5", "data": "run_now:sched-2026-09-25"},
}
_LLM_ONLY = ("unrecoverable:operator:anthropic:unrecoverable:http_400",)


class _Clock(datetime):
    moment = at(22, 30)

    @classmethod
    def now(cls, tz: tzinfo | None = None) -> datetime:  # type: ignore[override]
        return cls.moment


def _transport(calls: list[tuple[str, str]]) -> object:
    def send(token: str, method: str, payload: dict[str, object], _: float) -> object:
        calls.append((token, method))
        if method == "getUpdates":
            return {"ok": True, "result": [] if "offset" in payload else [_CALLBACK]}
        if method == "answerCallbackQuery":
            return {"ok": True, "result": True}
        return {"ok": True, "result": {"message_id": len(calls)}}

    return send


def _fire(
    monkeypatch: pytest.MonkeyPatch, graph: InMemoryGraphStore, hour: int, minute: int
) -> int:
    _Clock.moment = at(hour, minute)
    monkeypatch.setattr(entrypoint, "_live_graph", lambda: graph)
    return entrypoint.main(["--as-of", "2026-09-25", "--env-file", "missing.env"])


def test_the_bot_credential_never_leaves_the_port_on_any_path(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """DSP-SEC-01 / DSP-SEC-02: only the injected port ever holds the credential.

    A held run's notice, the operator's answer (poll, acknowledge, confirm), a
    degraded run's notice and the daily brief all go through the real client; the
    credential reaches its transport on every call and appears in no printed line
    and no graph fact. The dispatcher takes the port, never a token or a chat id.
    """
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr("orchestration.telegram_client.send_request", _transport(calls))
    monkeypatch.setattr(entrypoint, "datetime", _Clock)
    monkeypatch.setenv("POSTGRES_DSN", "postgresql://unused")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", _SENTINEL)
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "operator-chat")
    held = InMemoryGraphStore()
    preflight(held, passed=False, checked_at=at(22, 25))
    degraded = InMemoryGraphStore()
    preflight(degraded, passed=False, checked_at=at(22, 25), failures=_LLM_ONLY)
    briefed = InMemoryGraphStore()
    seed_pair(briefed)

    statuses = (
        _fire(monkeypatch, held, 22, 30),
        _fire(monkeypatch, held, 22, 40),
        _fire(monkeypatch, degraded, 22, 30),
        _fire(monkeypatch, briefed, 23, 30),
    )

    printed = capsys.readouterr()
    graphs = (held, degraded, briefed)
    facts = repr([dict(n.props) for g in graphs for n in g._nodes.values()])
    assert statuses == (0, 0, 0, 0)
    assert {method for _, method in calls} == {
        "sendMessage",
        "getUpdates",
        "answerCallbackQuery",
    }
    assert {token for token, _ in calls} == {_SENTINEL}
    assert len([m for _, m in calls if m == "sendMessage"]) == 3
    assert _SENTINEL not in printed.out + printed.err + facts
    parameters = inspect.signature(dispatch_with_human_answer).parameters
    assert not {"token", "api_token", "chat_id"} & set(parameters)
