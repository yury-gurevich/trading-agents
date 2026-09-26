"""S234 Telegram brief transport: plain text to the configured chat, failures as values.

Agent: orchestration
Role: prove `send_brief` at the port boundary, and what a refused send leaves behind.
External I/O: none; HTTPS is replaced by an injected sender.
"""

from __future__ import annotations

from dataclasses import dataclass

from kernel import InMemoryGraphStore
from orchestration.telegram_client import TelegramClient
from orchestration.tests.daily_brief_fixtures import at, fire
from orchestration.tests.daily_brief_scenarios import A1_TEXT, seed_pair
from orchestration.tests.scheduled_dispatch_human_helpers import FakeTelegram

_CREDENTIAL = "test"


def test_send_brief_posts_plain_text_to_the_configured_chat_only() -> None:
    """DSP-SEC-02: the brief leaves as plain text, only to the configured chat."""
    sent: list[tuple[str, dict[str, object]]] = []

    def sender(method: str, payload: dict[str, object], timeout: float) -> object:
        sent.append((method, payload))
        return {"ok": True, "result": {"message_id": 55}}

    client = TelegramClient(api_token=_CREDENTIAL, chat_id="operator", sender=sender)

    assert client.send_brief(text=A1_TEXT) == 55
    assert sent == [("sendMessage", {"chat_id": "operator", "text": A1_TEXT})]


def test_send_brief_failures_are_values_that_keep_the_transport_error() -> None:
    """DSP-STA-02 / DSP-FAIL-01: a failed send returns None and a named error.

    A transport exception keeps its type name; a reply with no message id says so.
    Neither raises.
    """
    raising = TelegramClient(
        api_token=_CREDENTIAL,
        chat_id="operator",
        sender=lambda _m, _p, _t: (_ for _ in ()).throw(TimeoutError()),
    )
    empty = TelegramClient(
        api_token=_CREDENTIAL,
        chat_id="operator",
        sender=lambda _m, _p, _t: {"ok": True, "result": {}},
    )

    assert raising.send_brief(text="x") is None
    assert raising.last_error == "TimeoutError"
    assert empty.send_brief(text="x") is None
    assert empty.last_error == "telegram_message_id_missing"


@dataclass
class _ChattyPort(FakeTelegram):
    last_error: str = "refused: Equity $101,976.32"


def test_a_refused_brief_leaves_the_ports_error_word_and_never_its_text() -> None:
    """DSP-STA-02 / DSP-SEC-02: a refused send is a fault naming the port's error.

    Telegram refusing the real client leaves `telegram_response_invalid`; a port
    whose error carries text is reduced to `no message id`, so no amount follows.
    """
    refused_graph = InMemoryGraphStore()
    seed_pair(refused_graph)
    chatty_graph = InMemoryGraphStore()
    seed_pair(chatty_graph)
    refused = TelegramClient(
        api_token=_CREDENTIAL,
        chat_id="operator",
        sender=lambda _m, _p, _t: {"ok": False},
    )

    fire(refused_graph, refused, at(22, 50))
    fire(chatty_graph, _ChattyPort(brief_returns_none=True), at(22, 50))

    (refusal,) = refused_graph.list_nodes("Fault")
    (chatter,) = chatty_graph.list_nodes("Fault")
    assert refusal.props["message"] == (
        "daily brief not sent for sched-2026-09-25: send failed "
        "(telegram_response_invalid)"
    )
    assert str(chatter.props["message"]).endswith("send failed (no message id)")
