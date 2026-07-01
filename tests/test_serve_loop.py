"""Tests for kernel.serve_loop.serve_once (the testable single pass) — S97."""

from __future__ import annotations

from typing import Any

from kernel.bus import InProcessBus
from kernel.envelope import AgentMessage
from kernel.serve_loop import LocalRequestConsumer, serve_once


def _request(sender: str, recipient: str, capability: str) -> AgentMessage:
    return AgentMessage(
        sender=sender,
        recipient=recipient,
        message_type="request",
        capability=capability,
        payload={"n": 2},
    )


def test_serve_once_dispatches_request_and_replies_with_response() -> None:
    bus = InProcessBus()
    bus.register("forecaster", "forecast", lambda p: {"doubled": p["n"] * 2})
    consumer = LocalRequestConsumer([_request("operator", "forecaster", "forecast")])

    count = serve_once(consumer, bus)

    assert count == 1
    (reply,) = consumer.replies
    assert reply.message_type == "response"
    assert reply.payload == {"doubled": 4}


def test_serve_once_rejects_unauthorized_caller() -> None:
    bus = InProcessBus()
    bus.register(
        "supervisor", "gate", lambda p: {"ok": True}, allowed_callers=("operator",)
    )
    consumer = LocalRequestConsumer([_request("scanner", "supervisor", "gate")])

    serve_once(consumer, bus)

    (reply,) = consumer.replies
    assert reply.message_type == "error"
    assert reply.payload["error_type"] == "Unauthorized"


def test_serve_once_returns_error_on_handler_fault_and_keeps_serving() -> None:
    def boom(_payload: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("handler exploded")

    bus = InProcessBus()
    bus.register("curator", "assemble", boom)
    consumer = LocalRequestConsumer()
    consumer.submit(_request("operator", "curator", "assemble"))

    count = serve_once(consumer, bus)  # must not raise

    assert count == 1
    (reply,) = consumer.replies
    assert reply.message_type == "error"


def test_serve_once_is_noop_on_empty_inbox() -> None:
    bus = InProcessBus()
    consumer = LocalRequestConsumer()

    count = serve_once(consumer, bus)

    assert count == 0
    assert consumer.replies == []
