"""In-process message bus for deterministic agent-to-agent requests.

Agent: kernel
Role: route validated message payloads to registered in-process handlers.
External I/O: none.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

from kernel.envelope import AgentMessage
from kernel.errors import CollectingFaultSink, FaultSink, fault_boundary

MessageHandler = Callable[[dict[str, Any]], dict[str, Any]]


class MessageBus(Protocol):
    """Transport-neutral request bus interface."""

    def register(
        self, recipient: str, capability: str, handler: MessageHandler
    ) -> None:
        """Register a handler for one recipient capability."""
        ...

    def request(self, message: AgentMessage) -> AgentMessage:
        """Send one request message and return a response or error message."""
        ...


class InProcessBus:
    """Synchronous bus backend used by tests and local runtime probes."""

    def __init__(self, sink: FaultSink | None = None) -> None:
        """Create an empty bus with an optional central fault sink."""
        self.sink = sink if sink is not None else CollectingFaultSink()
        self._handlers: dict[tuple[str, str], MessageHandler] = {}

    def register(
        self, recipient: str, capability: str, handler: MessageHandler
    ) -> None:
        """Register a handler for one recipient capability."""
        self._handlers[(recipient, capability)] = handler

    def request(self, message: AgentMessage) -> AgentMessage:
        """Dispatch a request and return a response, never raising handler faults."""
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
        return AgentMessage(
            sender=message.recipient,
            recipient=message.sender,
            message_type="response",
            capability=message.capability,
            payload=payload,
            correlation_id=message.id,
        )

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
