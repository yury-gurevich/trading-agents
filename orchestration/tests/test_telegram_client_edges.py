"""Telegram transport and callback edge tests for S219.

Agent: orchestration
Role: prove malformed Telegram responses degrade without dispatching a run.
External I/O: none; HTTPS is monkeypatched.
"""

from __future__ import annotations

import json
from importlib import import_module
from typing import TYPE_CHECKING
from urllib.request import Request

from orchestration.telegram_client import TelegramClient
from orchestration.telegram_http import send_request
from orchestration.telegram_updates import TelegramAnswer, parse_answer

if TYPE_CHECKING:
    import pytest


def test_client_handles_missing_id_non_list_and_acknowledgement() -> None:
    """S219: Telegram message and update shape defects do not create answers."""
    credential = "test"
    client = TelegramClient(
        api_token=credential,
        chat_id="chat",
        sender=lambda _method, _payload, _timeout: {"ok": True, "result": {}},
    )

    assert (
        client.send_hold_notice(run_id="run", failures=(), act_by="23:20 UTC") is None
    )
    assert client.last_error == "telegram_message_id_missing"
    assert client.poll_answers() == ()
    assert client.ack_button(callback_query_id="callback", text="Recorded") is True


def test_client_records_sender_and_response_failures() -> None:
    """S219: a transport exception and invalid response both return falsey values."""
    credential = "test"
    raising = TelegramClient(
        api_token=credential,
        chat_id="chat",
        sender=lambda _method, _payload, _timeout: (_ for _ in ()).throw(
            TimeoutError()
        ),
    )
    invalid = TelegramClient(
        api_token=credential,
        chat_id="chat",
        sender=lambda _method, _payload, _timeout: {"ok": False},
    )

    assert raising.confirm(up_to_update_id=1) is False
    assert raising.last_error == "TimeoutError"
    assert invalid.confirm(up_to_update_id=1) is False
    assert invalid.last_error == "telegram_response_invalid"


def test_callback_parser_rejects_each_invalid_shape_and_accepts_legal_data() -> None:
    """S219: only one of the two callback actions reaches the dispatcher."""
    assert parse_answer(None) is None
    assert parse_answer({"update_id": 1}) is None
    assert parse_answer({"update_id": 1, "callback_query": {"id": "q"}}) is None
    assert (
        parse_answer(
            {"update_id": 1, "callback_query": {"id": "q", "data": "later:run"}}
        )
        is None
    )
    assert parse_answer(
        {"update_id": 1, "callback_query": {"id": "q", "data": "run_now:run"}}
    ) == TelegramAnswer(1, "run_now", "run", "q")


def test_http_sender_posts_json_and_protocol_module_loads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """S219: default transport posts JSON and the typed port remains importable."""
    sent: dict[str, object] = {}

    class Response:
        def __enter__(self) -> Response:
            return self

        def __exit__(self, *_exc: object) -> None:
            return None

        def read(self) -> bytes:
            return b'{"ok": true}'

    def fake_urlopen(request: Request, timeout: float) -> Response:
        sent.update({"request": request, "timeout": timeout})
        return Response()

    module = import_module("orchestration.telegram_http")
    monkeypatch.setattr(module, "urlopen", fake_urlopen)

    assert send_request("test", "sendMessage", {"chat_id": "chat"}, 5.0) == {"ok": True}
    request = sent["request"]
    assert isinstance(request, Request)
    assert request.full_url.endswith("/botsendMessage") is False
    assert request.full_url.endswith("/sendMessage")
    assert isinstance(request.data, bytes)
    assert json.loads(request.data) == {"chat_id": "chat"}
    assert sent["timeout"] == 5.0
    assert (
        import_module("orchestration.telegram_port").TelegramPort.__name__
        == "TelegramPort"
    )
