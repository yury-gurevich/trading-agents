"""In-process message bus for deterministic agent-to-agent requests.

Agent: kernel
Role: route validated message payloads to registered in-process handlers; fan-out
      fire-and-forget pub/sub events to topic subscribers.
External I/O: none.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

from kernel.envelope import AgentMessage
from kernel.errors import CollectingFaultSink, FaultSink, fault_boundary
from kernel.metrics import Metrics, NullMetrics, request_metric

MessageHandler = Callable[[dict[str, Any]], dict[str, Any]]
EventHandler = Callable[[dict[str, Any]], None]


class MessageBus(Protocol):
    """Transport-neutral bus interface: synchronous RPC + fire-and-forget pub/sub."""

    def register(
        self, recipient: str, capability: str, handler: MessageHandler
    ) -> None:
        """Register a handler for one recipient capability."""
        ...  # pragma: no cover - protocol declaration only.

    def request(self, message: AgentMessage) -> AgentMessage:
        """Send one request message and return a response or error message."""
        ...  # pragma: no cover - protocol declaration only.

    def subscribe(self, topic: str, handler: EventHandler) -> None:
        """Register a handler to receive all events published to ``topic``."""
        ...  # pragma: no cover - protocol declaration only.

    def publish(self, topic: str, event: dict[str, Any]) -> None:
        """Deliver ``event`` synchronously to every subscriber on ``topic``."""
        ...  # pragma: no cover - protocol declaration only.


class InProcessBus:
    """Synchronous bus backend used by tests and local runtime probes."""

    def __init__(
        self, sink: FaultSink | None = None, metrics: Metrics | None = None
    ) -> None:
        """Create an empty bus with optional central fault and metrics sinks."""
        self.sink = sink if sink is not None else CollectingFaultSink()
        self.metrics = metrics if metrics is not None else NullMetrics()
        self._handlers: dict[tuple[str, str], MessageHandler] = {}
        self._subscribers: dict[str, list[EventHandler]] = {}

    def register(
        self, recipient: str, capability: str, handler: MessageHandler
    ) -> None:
        """Register a handler for one recipient capability."""
        self._handlers[(recipient, capability)] = handler

    def request(self, message: AgentMessage) -> AgentMessage:
        """Dispatch a request and return a response, never raising handler faults."""
        with request_metric(
            self.metrics, message.recipient, message.capability
        ) as metric:
            handler = self._handlers.get((message.recipient, message.capability))
            if handler is None:
                return self._error_message(
                    message,
                    error_type="UnknownCapability",
                    text=(
                        "No handler registered for "
                        f"{message.recipient}.{message.capability}"
                    ),
                )

            payload: dict[str, Any] = {}
            with fault_boundary(
                self.sink,
                agent=message.recipient,
                module="kernel.bus",
                capability=message.capability,
                reraise=False,
            ) as capture:
                payload = handler(message.payload)

            if capture.fault is not None:
                return self._error_message(
                    message,
                    error_type=capture.fault.error_type,
                    text=capture.fault.message,
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
        """Append ``handler`` to the subscriber list for ``topic``."""
        self._subscribers.setdefault(topic, []).append(handler)

    def publish(self, topic: str, event: dict[str, Any]) -> None:
        """Call every registered subscriber for ``topic`` with ``event``."""
        for handler in self._subscribers.get(topic, []):
            handler(event)

    @staticmethod
    def _error_message(
        message: AgentMessage, *, error_type: str, text: str
    ) -> AgentMessage:
        return AgentMessage(
            sender=message.recipient,
            recipient=message.sender,
            message_type="error",
            capability=message.capability,
            payload={"error_type": error_type, "message": text},
            correlation_id=message.id,
        )
