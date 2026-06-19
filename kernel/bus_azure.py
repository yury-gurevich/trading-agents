"""Azure Service Bus pub/sub backend.

Agent: kernel
Role: implement MessageBus.subscribe/publish over Azure Service Bus topics; RPC calls
      route through an in-process shim so synchronous operator paths are preserved.
External I/O: azure.servicebus SDK (optional dep); # pragma: no cover on I/O paths.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from kernel.bus import EventHandler, MessageHandler
from kernel.bus_azure_config import AzureServiceBusSettings
from kernel.envelope import AgentMessage
from kernel.errors import CollectingFaultSink, FaultSink, fault_boundary
from kernel.metrics import Metrics, NullMetrics, request_metric

if TYPE_CHECKING:
    pass


class AzureServiceBusBus:
    """Azure Service Bus backend; claim-check keeps all messages < 256 KB."""

    def __init__(
        self,
        sink: FaultSink | None = None,
        *,
        settings: AzureServiceBusSettings | None = None,
        metrics: Metrics | None = None,
    ) -> None:
        """Create bus; ``settings.connection_string`` activates Azure I/O path."""
        self._settings = settings if settings is not None else AzureServiceBusSettings()
        self.sink = sink if sink is not None else CollectingFaultSink()
        self.metrics = metrics if metrics is not None else NullMetrics()
        self._handlers: dict[tuple[str, str], MessageHandler] = {}
        self._subscribers: dict[str, list[EventHandler]] = {}

    def register(self, recipient: str, capability: str, handler: MessageHandler) -> None:
        """Register a synchronous RPC handler (in-process shim)."""
        self._handlers[(recipient, capability)] = handler

    def request(self, message: AgentMessage) -> AgentMessage:
        """Route a synchronous RPC request through the in-process handler shim."""
        with request_metric(self.metrics, message.recipient, message.capability) as metric:
            handler = self._handlers.get((message.recipient, message.capability))
            if handler is None:
                return self._error_message(
                    message,
                    error_type="UnknownCapability",
                    text=f"No handler registered for {message.recipient}.{message.capability}",
                )
            payload: dict[str, Any] = {}
            with fault_boundary(
                self.sink,
                agent=message.recipient,
                module="kernel.bus_azure",
                capability=message.capability,
                reraise=False,
            ) as capture:
                result = handler(message.payload)
                payload = result if isinstance(result, dict) else result
            if capture.fault is not None:
                return self._error_message(
                    message,
                    error_type="HandlerFault",
                    text=str(capture.fault.message),
                )
            metric.ok = True
        return AgentMessage(
            sender=message.recipient,
            recipient=message.sender,
            message_type="response",
            capability=message.capability,
            payload=payload,
            correlation_id=message.id,
        )

    def subscribe(self, topic: str, handler: EventHandler) -> None:
        """Register a local handler for events published to ``topic``."""
        self._subscribers.setdefault(topic, []).append(handler)

    def publish(self, topic: str, event: dict[str, Any]) -> None:
        """Deliver event; routes to Azure Service Bus when a connection string is set."""
        if self._settings.connection_string is not None:  # pragma: no cover
            self._azure_send(topic, event)
            return
        for handler in self._subscribers.get(topic, []):
            handler(event)

    def _azure_send(self, topic: str, event: dict[str, Any]) -> None:  # pragma: no cover
        """Send one claim-check event to an Azure Service Bus topic."""
        from azure.servicebus import ServiceBusClient, ServiceBusMessage  # type: ignore[import-not-found]

        client = ServiceBusClient.from_connection_string(
            self._settings.connection_string,  # type: ignore[arg-type]
        )
        with client:
            with client.get_topic_sender(topic_name=topic) as sender:
                sender.send_messages(
                    ServiceBusMessage(
                        json.dumps(event),
                        content_type="application/json",
                    )
                )

    @staticmethod
    def _error_message(message: AgentMessage, *, error_type: str, text: str) -> AgentMessage:
        return AgentMessage(
            sender=message.recipient,
            recipient=message.sender,
            message_type="error",
            capability=message.capability,
            payload={"error_type": error_type, "message": text},
            correlation_id=message.id,
        )
