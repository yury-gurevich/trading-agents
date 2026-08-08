"""Helpers for deliberator Service Bus reply-correlation tests.

Agent: deliberator
Role: build fake peer replies whose ready events can be ordered by tests.
External I/O: none.
"""

from __future__ import annotations

import json
import uuid

from tests.bus_azure_receiver_helpers import RawMessage

from agents.deliberator.peer_client import ServiceBusPeerClient
from contracts.deliberator import (
    DebateProposition,
    DebateTurnRecord,
    DebateTurnReply,
    DebateTurnRequest,
)
from kernel import (
    AgentMessage,
    AzureServiceBusSettings,
    GraphFaultSink,
    InMemoryGraphStore,
)

DEFAULT_REQUEST_ID = "pm-new:AAPL:defender:r1"
DEFAULT_REPLY_TEXT = "fresh AAPL reply"


def turn_request(request_id: str = DEFAULT_REQUEST_ID) -> DebateTurnRequest:
    return DebateTurnRequest(
        request_id=request_id,
        proposition=DebateProposition(decision="buy AAPL", context="ctx"),
        role="defender",
        round_number=1,
    )


def store_reply(
    graph: InMemoryGraphStore,
    ref: str,
    *,
    request_id: str,
    text: str,
    correlation_id: uuid.UUID,
) -> RawMessage:
    reply = AgentMessage(
        sender="deliberator-proponent",
        recipient="deliberator-manager",
        message_type="response",
        capability="debate_turn",
        payload=DebateTurnReply(
            request_id=request_id,
            turn=DebateTurnRecord(role="defender", round=1, text=text),
        ).model_dump(mode="json"),
        correlation_id=correlation_id,
    )
    graph.merge_node("AgentMessage", ref, reply.model_dump(mode="json"))
    return raw_ready(ref, str(correlation_id))


def raw_ready(ref: str, run_id: str) -> RawMessage:
    return RawMessage(
        json.dumps(
            {
                "topic": "deliberator-manager.reply",
                "label": "AgentMessage",
                "ref": ref,
                "run_id": run_id,
            }
        )
    )


class ReplyReceiver:
    def __init__(
        self,
        graph: InMemoryGraphStore,
        messages: list[RawMessage],
        *,
        fresh_ref: str | None = None,
        fresh_request_id: str = DEFAULT_REQUEST_ID,
        fresh_text: str = DEFAULT_REPLY_TEXT,
    ) -> None:
        self.graph = graph
        self.messages = messages
        self.fresh_ref = fresh_ref
        self.fresh_request_id = fresh_request_id
        self.fresh_text = fresh_text
        self.fresh_sent = False
        self.receive_calls = 0
        self.completed: list[RawMessage] = []
        self.dead_lettered: list[tuple[RawMessage, str]] = []

    def receive_messages(
        self, *, max_message_count: int, max_wait_time: float
    ) -> list[RawMessage]:
        del max_wait_time
        self.receive_calls += 1
        if self.messages:
            batch = self.messages[:max_message_count]
            self.messages = self.messages[max_message_count:]
            return batch
        if self.fresh_ref is None or self.fresh_sent:
            return []
        self.fresh_sent = True
        return [
            store_reply(
                self.graph,
                self.fresh_ref,
                request_id=self.fresh_request_id,
                text=self.fresh_text,
                correlation_id=published_request_id(self.graph),
            )
        ]

    def complete_message(self, message: RawMessage) -> None:
        self.completed.append(message)

    def dead_letter_message(self, message: RawMessage, *, reason: str) -> None:
        self.dead_lettered.append((message, reason))


def published_request_id(graph: InMemoryGraphStore) -> uuid.UUID:
    for node in graph.list_nodes("AgentMessage"):
        if node.props.get("message_type") == "request":
            return uuid.UUID(str(node.props["id"]))
    raise AssertionError("request was not claim-checked")


def client(
    graph: InMemoryGraphStore, receiver: ReplyReceiver, sink: GraphFaultSink
) -> ServiceBusPeerClient:
    return ServiceBusPeerClient(
        graph,
        sender="deliberator-manager",
        settings=AzureServiceBusSettings(
            connection_string=None,
            connection_strings_json=None,
        ),
        timeout_seconds=1.0,
        reply_receiver=receiver,
        sink=sink,
    )
