"""Base class binding agent contracts to the message bus.

Agent: kernel
Role: validate contract payloads and dispatch to subclass capability handlers.
External I/O: none.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

if TYPE_CHECKING:
    from kernel.bus import MessageBus, MessageHandler
    from kernel.contract import AgentContract, Capability

AgentHandler = Callable[[BaseModel], object]


class AgentBase:
    """Contract-bound base class for in-process agent handlers."""

    def __init__(self, contract: AgentContract, bus: MessageBus) -> None:
        """Store the contract and bus; subclasses provide the handler map."""
        self.contract = contract
        self.bus = bus
        self.handlers: Mapping[str, AgentHandler] = {}

    def bind(self) -> None:
        """Register this agent's consumed capabilities with the message bus."""
        for capability in self.contract.consumes:
            self.bus.register(
                self.contract.name,
                capability.name,
                self._bus_handler(capability, self.handlers[capability.name]),
                capability.allowed_callers,
            )

    @staticmethod
    def _bus_handler(capability: Capability, handler: AgentHandler) -> MessageHandler:
        def wrapped(payload: dict[str, Any]) -> dict[str, Any]:
            request_model = capability.request.model_validate(payload)
            result = handler(request_model)
            response_model = capability.response.model_validate(result)
            return response_model.model_dump(mode="json")

        return wrapped
