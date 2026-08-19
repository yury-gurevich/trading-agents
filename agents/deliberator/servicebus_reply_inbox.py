"""Concurrent Service Bus reply routing for the deliberator manager.

Agent: deliberator
Role: keep sibling in-flight peer replies from being misclassified as orphans.
External I/O: Azure Service Bus receiver protocol supplied by caller.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from threading import Lock
from typing import TYPE_CHECKING, Any

from kernel.bus_azure_ready import (
    ORPHANED_READY_EVENT_REASON,
    CorrelatedReadyEvent,
    CorrelatedReadyEventTimeoutError,
    ReadyEventReceiver,
    ready_event_from_raw,
)

REPLY_RECEIVE_SLICE_SECONDS = 1.0

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


class ServiceBusReplyInbox:
    """Route ready events among concurrent manager waits by correlation id."""

    def __init__(self) -> None:
        """Create an empty in-process router for pending ready events."""
        self._lock = Lock()
        self._pending: set[str] = set()
        self._stashed: dict[str, dict[str, Any]] = {}

    @contextmanager
    def expecting(self, correlation_id: str) -> Iterator[None]:
        """Mark a request id as in-flight before its request is published."""
        with self._lock:
            self._pending.add(correlation_id)
        try:
            yield
        finally:
            with self._lock:
                self._pending.discard(correlation_id)
                self._stashed.pop(correlation_id, None)

    def receive[MessageT](
        self,
        receiver: ReadyEventReceiver[MessageT],
        *,
        correlation_id: str,
        deadline: float,
        now: Callable[[], float] = time.monotonic,
    ) -> CorrelatedReadyEvent:
        """Receive this request's ready event, stashing sibling events."""
        orphan_count = 0
        while True:
            stashed = self._pop(correlation_id)
            if stashed is not None:
                return CorrelatedReadyEvent(stashed, orphan_count)
            remaining = deadline - now()
            if remaining <= 0:
                raise CorrelatedReadyEventTimeoutError(correlation_id, orphan_count)
            wait_time = min(remaining, REPLY_RECEIVE_SLICE_SECONDS)
            messages = receiver.receive_messages(
                max_message_count=1,
                max_wait_time=wait_time,
            )
            if not messages:
                stashed = self._pop(correlation_id)
                if stashed is not None:
                    return CorrelatedReadyEvent(stashed, orphan_count)
                if wait_time >= remaining:
                    raise CorrelatedReadyEventTimeoutError(correlation_id, orphan_count)
                continue
            raw = messages[0]
            event = _event_or_none(raw)
            if event is None:
                receiver.dead_letter_message(raw, reason=ORPHANED_READY_EVENT_REASON)
                orphan_count += 1
                continue
            run_id = _run_id(event)
            if run_id == correlation_id:
                receiver.complete_message(raw)
                return CorrelatedReadyEvent(event, orphan_count)
            if run_id is not None and self._is_pending(run_id):
                receiver.complete_message(raw)
                self._stash(run_id, event)
                continue
            receiver.dead_letter_message(raw, reason=ORPHANED_READY_EVENT_REASON)
            orphan_count += 1

    def _pop(self, correlation_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._stashed.pop(correlation_id, None)

    def _is_pending(self, correlation_id: str) -> bool:
        with self._lock:
            return correlation_id in self._pending

    def _stash(self, correlation_id: str, event: dict[str, Any]) -> None:
        with self._lock:
            self._stashed[correlation_id] = event


def _event_or_none(raw: object) -> dict[str, Any] | None:
    try:
        return ready_event_from_raw(raw)
    except (TypeError, ValueError):
        return None


def _run_id(event: dict[str, Any]) -> str | None:
    run_id = event.get("run_id")
    return run_id if isinstance(run_id, str) else None
