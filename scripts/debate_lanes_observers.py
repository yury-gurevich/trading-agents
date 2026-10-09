"""The two passive observers of the debate lanes harness.

Agent: tooling
Role: record serving and manager calls without altering requests or replies.
External I/O: none; injected ports own transport I/O.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import threading

    from agents.deliberator.servicebus_peer_client import ServiceBusPeerClient
    from contracts.deliberator import DebateTurnReply, DebateTurnRequest
    from kernel import AgentMessage, InProcessBus


class TimedBus:
    """Observe each replica's served request and leave its message untouched."""

    def __init__(
        self,
        inner: InProcessBus,
        replica: str,
        log: list[dict[str, Any]],
        lock: threading.Lock,
    ) -> None:
        self._inner, self._replica, self._log, self._lock = inner, replica, log, lock

    def request(self, message: AgentMessage) -> AgentMessage:
        started = time.monotonic()
        try:
            return self._inner.request(message)
        finally:
            ended = time.monotonic()
            with self._lock:
                self._log.append(
                    {
                        "request_id": message.payload.get("request_id"),
                        "replica": self._replica,
                        "start": started,
                        "end": ended,
                    }
                )


class CheckingPeerClient:
    """Observe manager waits and replies, including a reply for another id."""

    def __init__(
        self,
        inner: ServiceBusPeerClient,
        log: list[dict[str, Any]],
        lock: threading.Lock,
    ) -> None:
        self._inner, self._log, self._lock = inner, log, lock

    @property
    def orphaned_reply_count(self) -> int:
        return self._inner.orphaned_reply_count

    def preflight(self, recipients: tuple[str, ...]) -> None:
        self._inner.preflight(recipients)

    def debate_turn(
        self, recipient: str, request: DebateTurnRequest
    ) -> DebateTurnReply:
        row: dict[str, Any] = {
            "request_id": request.request_id,
            "call": time.monotonic(),
            "outcome": "raised",
        }
        try:
            reply = self._inner.debate_turn(recipient, request)
            row["outcome"] = (
                "answered" if reply.request_id == request.request_id else "mismatched"
            )
            return reply
        finally:
            row["return"] = time.monotonic()
            with self._lock:
                self._log.append(row)
