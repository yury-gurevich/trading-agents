"""Deliberator peer request clients.

Agent: deliberator
Role: let the manager request one turn from served proponent/opponent instances.
External I/O: Azure Service Bus only when ServiceBusPeerClient is used.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from agents.deliberator.servicebus_peer_client import ServiceBusPeerClient
from contracts.deliberator import DebateTurnReply, DebateTurnRequest
from kernel import AgentMessage

if TYPE_CHECKING:
    from kernel import MessageBus

__all__ = ["BusPeerClient", "PeerClient", "ServiceBusPeerClient"]


def orphaned_reply_count_from(peer_client: object) -> int:
    """Return a peer client's cumulative orphan count when it exposes one."""
    value = getattr(peer_client, "orphaned_reply_count", 0)
    return value if isinstance(value, int) else 0


class PeerClient(Protocol):
    """Transport-neutral manager port for one debate-turn request."""

    def preflight(self, recipients: tuple[str, ...]) -> None:
        """Raise if a peer cannot be addressed before PM work is consumed."""
        ...  # pragma: no cover - protocol declaration only.

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

    def preflight(self, recipients: tuple[str, ...]) -> None:
        """Local in-process peers are addressable through the injected bus."""
        del recipients

    @property
    def orphaned_reply_count(self) -> int:
        """Return no late replies for the local in-process peer transport."""
        return 0

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
