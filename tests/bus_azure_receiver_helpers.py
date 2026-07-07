"""Helpers for Azure Service Bus receiver tests.

Agent: kernel
Role: provide fake Service Bus messages/receivers and claim-check fixtures.
External I/O: none.
"""

from __future__ import annotations

import json
from typing import Any

from kernel import (
    AgentMessage,
    AzureServiceBusBus,
    AzureServiceBusSettings,
    InMemoryGraphStore,
    claim_check_write,
)


class RawMessage:
    def __init__(self, body: Any, *, delivery_count: Any = 1) -> None:
        self.body = body
        self.delivery_count = delivery_count


class FakeReceiver:
    def __init__(self, messages: list[RawMessage]) -> None:
        self.messages = messages
        self.completed: list[RawMessage] = []
        self.abandoned: list[RawMessage] = []
        self.dead_lettered: list[tuple[RawMessage, str]] = []

    def receive_messages(
        self, *, max_message_count: int, max_wait_time: float
    ) -> list[RawMessage]:
        del max_wait_time
        batch = self.messages[:max_message_count]
        self.messages = self.messages[max_message_count:]
        return batch

    def complete_message(self, message: RawMessage) -> None:
        self.completed.append(message)

    def abandon_message(self, message: RawMessage) -> None:
        self.abandoned.append(message)

    def dead_letter_message(self, message: RawMessage, *, reason: str) -> None:
        self.dead_lettered.append((message, reason))


class FailingPublishBus:
    def publish(self, topic: str, event: dict[str, Any]) -> None:
        del topic, event
        raise RuntimeError("publish unavailable")


def settings(**overrides: Any) -> AzureServiceBusSettings:
    values: dict[str, Any] = {
        "connection_string": None,
        "receive_max_messages": 10,
        "receive_timeout_seconds": 0.1,
        "max_delivery_count": 3,
        "reply_topic_suffix": ".reply",
    }
    values.update(overrides)
    return AzureServiceBusSettings(_env_file=None, **values)


def request(ref: str = "one") -> AgentMessage:
    return AgentMessage(
        sender="operator",
        recipient="echo",
        message_type="request",
        capability="echo",
        payload={"ref": ref},
    )


def response(message: AgentMessage) -> AgentMessage:
    return AgentMessage(
        sender="echo",
        recipient="operator",
        message_type="response",
        capability="echo",
        payload={"ref": message.payload["ref"], "ok": True},
        correlation_id=message.id,
    )


def raw_ready(
    graph: InMemoryGraphStore,
    bus: AzureServiceBusBus,
    message: AgentMessage,
    *,
    body_style: str = "text",
) -> RawMessage:
    event = claim_check_write(
        bus,
        graph,
        topic="echo.requests",
        label="AgentMessage",
        ref=str(message.id),
        props=message.model_dump(mode="json"),
    )
    text = json.dumps(event.model_dump(mode="json"))
    if body_style == "bytes":
        return RawMessage(text.encode("utf-8"))
    if body_style == "chunks":
        return RawMessage([text[:10], text[10:].encode("utf-8")])
    return RawMessage(text)
