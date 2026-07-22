"""Azure Service Bus request consumer.

Agent: kernel
Role: adapt a Service Bus topic subscription to the RequestConsumer protocol,
      resolving claim-check ready events into AgentMessage requests and publishing
      claim-checked response ready events back to the requester.
External I/O: azure.servicebus SDK when a connection string is configured.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Any, Protocol

from pydantic import ValidationError

from kernel.bus_azure_config import AzureServiceBusSettings
from kernel.claim_check import claim_check_read, claim_check_write
from kernel.envelope import AgentMessage

if TYPE_CHECKING:
    from uuid import UUID

    from kernel.bus import MessageBus
    from kernel.graph import GraphStore

_MESSAGE_LABEL = "AgentMessage"


class _ServiceBusReceiver(Protocol):
    """Small structural slice of the Azure SDK receiver used by this module."""

    def receive_messages(
        self, *, max_message_count: int, max_wait_time: float
    ) -> Sequence[Any]: ...  # pragma: no cover - protocol declaration only.

    def complete_message(
        self, message: object
    ) -> None: ...  # pragma: no cover - protocol declaration only.

    def abandon_message(
        self, message: object
    ) -> None: ...  # pragma: no cover - protocol declaration only.

    def dead_letter_message(
        self, message: object, *, reason: str
    ) -> None: ...  # pragma: no cover - protocol declaration only.


class AzureServiceBusRequestConsumer:
    """Service Bus receiver implementing ``RequestConsumer`` for served agents."""

    def __init__(
        self,
        bus: MessageBus,
        graph: GraphStore,
        *,
        topic: str,
        subscription_name: str,
        settings: AzureServiceBusSettings | None = None,
        reply_topic: str | None = None,
        receiver: _ServiceBusReceiver | None = None,
    ) -> None:
        """Bind one topic subscription to a graph-backed request inbox."""
        self._bus = bus
        self._graph = graph
        self._topic = topic
        self._subscription_name = subscription_name
        self._settings = settings if settings is not None else AzureServiceBusSettings()
        self._reply_topic = reply_topic
        self._receiver = receiver
        self._client: object | None = None
        self._pending: dict[UUID, object] = {}

    def poll(self) -> list[AgentMessage]:
        """Receive ready events and return their claim-checked request envelopes."""
        requests: list[AgentMessage] = []
        for raw in self._receive_messages():
            try:
                event = _ready_event(raw)
                node = claim_check_read(self._graph, event)
                request = AgentMessage.model_validate(dict(node.props))
            except (RuntimeError, TypeError, ValueError, ValidationError):
                self._reject(raw)
                continue
            self._pending[request.id] = raw
            requests.append(request)
        return requests

    def reply(self, response: AgentMessage) -> None:
        """Publish a claim-checked response and ack/abandon the source message."""
        correlation_id = response.correlation_id
        raw = self._pending.get(correlation_id) if correlation_id is not None else None
        try:
            self._publish_response(response)
        except Exception:
            if raw is not None and correlation_id is not None:
                self._reject(raw)
                self._pending.pop(correlation_id, None)
            return
        if raw is not None and correlation_id is not None:
            self._complete(raw)
            self._pending.pop(correlation_id, None)

    def _receive_messages(self) -> list[object]:
        """Pull a batch from the injected receiver or the live SDK receiver."""
        if self._receiver is None:
            if self._settings.connection_string_for_topic(self._topic) is None:
                return []
            self._receiver = self._open_receiver()  # pragma: no cover
        return list(
            self._receiver.receive_messages(
                max_message_count=self._settings.receive_max_messages,
                max_wait_time=self._settings.receive_timeout_seconds,
            )
        )

    def _open_receiver(self) -> _ServiceBusReceiver:  # pragma: no cover
        from azure.servicebus import ServiceBusClient

        connection_string = self._settings.connection_string_for_topic(self._topic)
        if connection_string is None:
            raise RuntimeError("Service Bus connection string is required")
        client = ServiceBusClient.from_connection_string(connection_string)
        self._client = client
        receiver: _ServiceBusReceiver = client.get_subscription_receiver(
            topic_name=self._topic,
            subscription_name=self._subscription_name,
        )
        return receiver

    def _publish_response(self, response: AgentMessage) -> None:
        """Store the response envelope in the graph and publish its ready event."""
        claim_check_write(
            self._bus,
            self._graph,
            topic=self._response_topic(response),
            label=_MESSAGE_LABEL,
            ref=str(response.id),
            props=response.model_dump(mode="json"),
            run_id=(
                str(response.correlation_id)
                if response.correlation_id is not None
                else None
            ),
        )

    def _response_topic(self, response: AgentMessage) -> str:
        """Return the configured reply topic for a response envelope."""
        if self._reply_topic is not None:
            return self._reply_topic
        return f"{response.recipient}{self._settings.reply_topic_suffix}"

    def _complete(self, raw: object) -> None:
        """Complete a successfully served request message."""
        assert self._receiver is not None
        self._receiver.complete_message(raw)

    def _reject(self, raw: object) -> None:
        """Abandon or dead-letter a failed request message."""
        assert self._receiver is not None
        if _delivery_count(raw) >= self._settings.max_delivery_count:
            self._receiver.dead_letter_message(raw, reason="S100ReceiverFailure")
            return
        self._receiver.abandon_message(raw)


def _ready_event(raw: object) -> dict[str, Any]:
    """Decode a raw Service Bus message body into a ready-event dict."""
    data = json.loads(_body_text(raw))
    if not isinstance(data, dict):
        raise ValueError("Service Bus ready event must be a JSON object")
    return data


def _body_text(raw: object) -> str:
    """Return the JSON body text from SDK messages and lightweight fakes."""
    body = getattr(raw, "body", raw)
    if isinstance(body, bytes):
        return body.decode("utf-8")
    if isinstance(body, str):
        return body
    if isinstance(body, Iterable):
        return "".join(_chunk_text(chunk) for chunk in body)
    return str(body)


def _chunk_text(chunk: object) -> str:
    return chunk.decode("utf-8") if isinstance(chunk, bytes) else str(chunk)


def _delivery_count(raw: object) -> int:
    try:
        return int(getattr(raw, "delivery_count", 1))
    except (TypeError, ValueError):
        return 1
