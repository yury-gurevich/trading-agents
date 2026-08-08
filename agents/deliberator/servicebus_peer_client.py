"""Service Bus deliberator peer request client.

Agent: deliberator
Role: publish manager peer requests and resolve only their correlated replies.
External I/O: Azure Service Bus only when live SDK receiver is opened.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from contracts.deliberator import DebateTurnReply, DebateTurnRequest
from kernel import (
    AgentFault,
    AgentMessage,
    AzureServiceBusBus,
    AzureServiceBusSettings,
    CollectingFaultSink,
    claim_check_read,
    claim_check_write,
)
from kernel.bus_azure_ready import (
    CorrelatedReadyEvent,
    CorrelatedReadyEventTimeoutError,
    ReadyEventReceiver,
    receive_correlated_ready_event,
)
from kernel.serve_transport import request_topic

if TYPE_CHECKING:
    from kernel import FaultSink, GraphStore

_MESSAGE_LABEL = "AgentMessage"


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
        reply_receiver: ReadyEventReceiver | None = None,
        sink: FaultSink | None = None,
    ) -> None:
        """Create a live Service Bus request client for the manager."""
        self._settings = settings if settings is not None else AzureServiceBusSettings()
        self._bus = AzureServiceBusBus(settings=self._settings)
        self._graph = graph
        self._sender = sender
        self._reply_subscription = reply_subscription
        self._timeout_seconds = timeout_seconds
        self._reply_receiver = reply_receiver
        self._sink = sink if sink is not None else CollectingFaultSink()
        self._orphaned_reply_count = 0

    @property
    def orphaned_reply_count(self) -> int:
        """Return reply events dead-lettered while resolving peer calls."""
        return self._orphaned_reply_count

    def preflight(self, recipients: tuple[str, ...]) -> None:
        """Resolve every peer request topic before consuming append-only work."""
        for recipient in recipients:
            topic = request_topic(recipient)
            self._settings.connection_string_for_topic(topic)

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
        self._publish_request(recipient, request, message)
        try:
            matched = self._read_ready_event(str(message.id))
        except CorrelatedReadyEventTimeoutError as exc:
            self._record_orphans(exc.orphan_count, message, request, recipient)
            raise RuntimeError("no deliberator peer reply received") from exc
        self._record_orphans(matched.orphan_count, message, request, recipient)
        node = claim_check_read(self._graph, matched.event)
        reply = AgentMessage.model_validate(dict(node.props))
        if reply.message_type == "error":
            raise RuntimeError(str(reply.payload.get("message", "peer call failed")))
        return DebateTurnReply.model_validate(reply.payload)

    def _publish_request(
        self, recipient: str, request: DebateTurnRequest, message: AgentMessage
    ) -> None:
        claim_check_write(
            self._bus,
            self._graph,
            topic=request_topic(recipient),
            label=_MESSAGE_LABEL,
            ref=str(message.id),
            props=message.model_dump(mode="json"),
            run_id=request.request_id,
        )

    def _read_ready_event(self, correlation_id: str) -> CorrelatedReadyEvent:
        if self._reply_receiver is not None:
            return receive_correlated_ready_event(
                self._reply_receiver,
                correlation_id=correlation_id,
                deadline=self._reply_deadline(),
            )
        return self._read_live_ready_event(correlation_id)  # pragma: no cover

    def _read_live_ready_event(
        self, correlation_id: str
    ) -> CorrelatedReadyEvent:  # pragma: no cover
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
            return receive_correlated_ready_event(
                receiver,
                correlation_id=correlation_id,
                deadline=self._reply_deadline(),
            )

    def _reply_deadline(self) -> float:
        timeout_seconds = (
            self._timeout_seconds
            if self._timeout_seconds is not None
            else self._settings.receive_timeout_seconds
        )
        return time.monotonic() + timeout_seconds

    def _record_orphans(
        self,
        orphan_count: int,
        message: AgentMessage,
        request: DebateTurnRequest,
        recipient: str,
    ) -> None:
        if orphan_count == 0:
            return
        self._orphaned_reply_count += orphan_count
        self._sink.submit(
            AgentFault(
                source_agent=self._sender,
                source_module="agents.deliberator.servicebus_peer_client",
                capability="debate_turn",
                severity="warning",
                error_type="OrphanedPeerReply",
                message=(
                    f"dead-lettered {orphan_count} orphaned peer reply "
                    f"ready event(s) while waiting for {recipient} "
                    f"{request.request_id}"
                ),
                correlation_id=str(message.id),
                context={
                    "orphan_count": orphan_count,
                    "recipient": recipient,
                    "request_id": request.request_id,
                },
            )
        )
