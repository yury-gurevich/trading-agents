"""Deliberator peer request clients.

Agent: deliberator
Role: let the manager request one turn from served proponent/opponent instances.
External I/O: Azure Service Bus only when ServiceBusPeerClient is used.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Protocol

from contracts.deliberator import DebateTurnReply, DebateTurnRequest
from kernel import (
    AgentMessage,
    AzureServiceBusBus,
    AzureServiceBusSettings,
    claim_check_read,
    claim_check_write,
)
from kernel.serve_transport import request_topic

if TYPE_CHECKING:
    from kernel import GraphStore, MessageBus

_MESSAGE_LABEL = "AgentMessage"


class PeerClient(Protocol):
    """Transport-neutral manager port for one debate-turn request."""

    def debate_turn(
        self, recipient: str, request: DebateTurnRequest
    ) -> DebateTurnReply:
        """Return one peer debate turn or raise so the manager can fail open."""
        ...  # pragma: no cover - protocol declaration only.


class BusPeerClient:
    """Request peers through an already-bound in-process bus."""

    def __init__(self, bus: MessageBus, *, sender: str) -> None:
        """Create a request client using a concrete manager sender identity."""
        self._bus = bus
        self._sender = sender

    def debate_turn(
        self, recipient: str, request: DebateTurnRequest
    ) -> DebateTurnReply:
        """Send one synchronous debate-turn request over the injected bus."""
        reply = self._bus.request(
            AgentMessage(
                sender=self._sender,
                recipient=recipient,
                message_type="request",
                capability="debate_turn",
                payload=request.model_dump(mode="json"),
            )
        )
        if reply.message_type == "error":
            raise RuntimeError(str(reply.payload.get("message", "peer call failed")))
        return DebateTurnReply.model_validate(reply.payload)


class ServiceBusPeerClient:
    """Publish claim-checked peer requests and wait for claim-checked replies."""

    def __init__(
        self,
        graph: GraphStore,
        *,
        sender: str,
        settings: AzureServiceBusSettings | None = None,
        reply_subscription: str = "agent",
        timeout_seconds: float | None = None,
    ) -> None:
        """Create a live Service Bus request client for the manager."""
        self._settings = settings if settings is not None else AzureServiceBusSettings()
        self._bus = AzureServiceBusBus(settings=self._settings)
        self._graph = graph
        self._sender = sender
        self._reply_subscription = reply_subscription
        self._timeout_seconds = timeout_seconds

    def debate_turn(
        self, recipient: str, request: DebateTurnRequest
    ) -> DebateTurnReply:
        """Publish the request-ready event and resolve the peer reply."""
        message = AgentMessage(
            sender=self._sender,
            recipient=recipient,
            message_type="request",
            capability="debate_turn",
            payload=request.model_dump(mode="json"),
        )
        topic = request_topic(recipient)
        claim_check_write(
            self._bus,
            self._graph,
            topic=topic,
            label=_MESSAGE_LABEL,
            ref=str(message.id),
            props=message.model_dump(mode="json"),
            run_id=request.request_id,
        )
        ready = self._read_ready_event()
        node = claim_check_read(self._graph, ready)
        reply = AgentMessage.model_validate(dict(node.props))
        if reply.message_type == "error":
            raise RuntimeError(str(reply.payload.get("message", "peer call failed")))
        return DebateTurnReply.model_validate(reply.payload)

    def _read_ready_event(self) -> dict[str, Any]:  # pragma: no cover
        from azure.servicebus import ServiceBusClient

        topic = f"{self._sender}{self._settings.reply_topic_suffix}"
        connection_string = self._settings.connection_string_for_topic(topic)
        if connection_string is None:
            raise RuntimeError("Service Bus connection string is required")
        client = ServiceBusClient.from_connection_string(connection_string)
        with (
            client,
            client.get_subscription_receiver(
                topic_name=topic,
                subscription_name=self._reply_subscription,
            ) as receiver,
        ):
            messages = receiver.receive_messages(
                max_message_count=1,
                max_wait_time=(
                    self._timeout_seconds
                    if self._timeout_seconds is not None
                    else self._settings.receive_timeout_seconds
                ),
            )
            if not messages:
                raise RuntimeError("no deliberator peer reply received")
            raw = messages[0]
            receiver.complete_message(raw)
            data = json.loads(_body_text(raw))
            if not isinstance(data, dict):
                raise RuntimeError("peer reply ready event was not an object")
            return data


def _body_text(raw: object) -> str:  # pragma: no cover
    body = getattr(raw, "body", raw)
    if isinstance(body, bytes):
        return body.decode("utf-8")
    if isinstance(body, str):
        return body
    if isinstance(body, Iterable):
        return "".join(_chunk_text(chunk) for chunk in body)
    return str(body)


def _chunk_text(chunk: object) -> str:  # pragma: no cover
    return chunk.decode("utf-8") if isinstance(chunk, bytes) else str(chunk)
