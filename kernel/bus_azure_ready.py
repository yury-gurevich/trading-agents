"""Azure Service Bus ready-event helpers.

Agent: kernel
Role: decode claim-check ready events and receive request-correlated replies.
External I/O: Azure Service Bus receiver protocol supplied by callers.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

ORPHANED_READY_EVENT_REASON = "S171OrphanedReply"


class ReadyEventReceiver[MessageT](Protocol):
    """Small receiver slice needed for correlated ready-event resolution."""

    def receive_messages(
        self, *, max_message_count: int, max_wait_time: float
    ) -> Sequence[MessageT]:
        """Receive raw Service Bus messages."""
        ...  # pragma: no cover - protocol declaration only.

    def complete_message(self, message: MessageT) -> None:
        """Complete a raw message that matched the requested correlation id."""
        ...  # pragma: no cover - protocol declaration only.

    def dead_letter_message(self, message: MessageT, *, reason: str) -> None:
        """Dead-letter a raw message that cannot answer this request."""
        ...  # pragma: no cover - protocol declaration only.


@dataclass(frozen=True)
class CorrelatedReadyEvent:
    """A matching ready event plus the skipped orphan count."""

    event: dict[str, Any]
    orphan_count: int


class CorrelatedReadyEventTimeoutError(RuntimeError):
    """Raised when no ready event matches the requested correlation id."""

    def __init__(self, correlation_id: str, orphan_count: int) -> None:
        """Record the missed id and how many orphans were skipped first."""
        self.correlation_id = correlation_id
        self.orphan_count = orphan_count
        super().__init__(
            f"no Service Bus ready event matched correlation_id {correlation_id}"
        )


def ready_event_from_raw(raw: object) -> dict[str, Any]:
    """Decode a raw Service Bus message body into a ready-event dict."""
    data = json.loads(_body_text(raw))
    if not isinstance(data, dict):
        raise ValueError("Service Bus ready event must be a JSON object")
    return data


def receive_correlated_ready_event[MessageT](
    receiver: ReadyEventReceiver[MessageT],
    *,
    correlation_id: str,
    deadline: float,
    now: Callable[[], float] = time.monotonic,
) -> CorrelatedReadyEvent:
    """Receive until a ready event's ``run_id`` matches ``correlation_id``."""
    orphan_count = 0
    while True:
        remaining = deadline - now()
        if remaining <= 0:
            raise CorrelatedReadyEventTimeoutError(correlation_id, orphan_count)
        messages = receiver.receive_messages(
            max_message_count=1,
            max_wait_time=remaining,
        )
        if not messages:
            raise CorrelatedReadyEventTimeoutError(correlation_id, orphan_count)
        raw = messages[0]
        event = _event_or_none(raw)
        if event is not None and event.get("run_id") == correlation_id:
            receiver.complete_message(raw)
            return CorrelatedReadyEvent(event, orphan_count)
        receiver.dead_letter_message(raw, reason=ORPHANED_READY_EVENT_REASON)
        orphan_count += 1


def _event_or_none(raw: object) -> dict[str, Any] | None:
    try:
        return ready_event_from_raw(raw)
    except (TypeError, ValueError):
        return None


def _body_text(raw: object) -> str:
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
