"""Serve/consume loop for RPC-triggered agent entrypoints — the pull side's twin.

Agent: kernel
Role: shared "receive a request -> dispatch to the bound handler -> reply" loop so
      every RPC-served agent entrypoint stays thin (DL-30 / DL-35). Dispatch is
      delegated to the bus's own ``request`` — reusing its capability lookup, the
      caller-authorization gate, and the fault boundary — so serving and calling
      share one code path and the loop can never die on a bad request. ``serve_once``
      carries the coverage; ``serve_loop`` is the infinite wrapper (twin of
      ``work_loop`` on the graph-pull side).
External I/O: none (the injected RequestConsumer owns any transport I/O).
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from kernel.bus import MessageBus
    from kernel.envelope import AgentMessage

_DEFAULT_POLL_INTERVAL = 60


class RequestConsumer(Protocol):
    """Transport-neutral inbox: pull pending requests, reply to their senders."""

    def poll(self) -> list[AgentMessage]:
        """Return any pending request messages (empty when idle)."""
        ...  # pragma: no cover - protocol declaration only.

    def reply(self, response: AgentMessage) -> None:
        """Deliver a response/error message back to the requester."""
        ...  # pragma: no cover - protocol declaration only.


class LocalRequestConsumer:
    """In-process inbox for tests and the local runtime shim.

    Requests are queued via ``submit`` (or seeded at construction); ``poll`` drains
    the queue; replies are captured on ``replies`` for inspection. The Service Bus
    receiver (S100) implements the same ``RequestConsumer`` protocol over a
    subscription, so ``serve_once`` is unchanged when the transport swaps.
    """

    def __init__(self, requests: list[AgentMessage] | None = None) -> None:
        """Seed the inbox with optional pending requests; start with no replies."""
        self._inbox: list[AgentMessage] = list(requests) if requests else []
        self.replies: list[AgentMessage] = []

    def submit(self, message: AgentMessage) -> None:
        """Enqueue one request to be returned by the next ``poll``."""
        self._inbox.append(message)

    def poll(self) -> list[AgentMessage]:
        """Drain and return every currently-queued request."""
        pending, self._inbox = self._inbox, []
        return pending

    def reply(self, response: AgentMessage) -> None:
        """Capture a response/error message addressed back to the requester."""
        self.replies.append(response)


def serve_once(consumer: RequestConsumer, bus: MessageBus) -> int:
    """Dispatch every pending request through the bus and reply; return the count.

    Each request is routed via ``bus.request`` — which enforces the capability
    matrix and never raises (handler faults come back as error messages) — so a
    single bad request can never kill the serving loop.
    """
    requests = consumer.poll()
    for request in requests:
        consumer.reply(bus.request(request))
    return len(requests)


def serve_loop(  # pragma: no cover - blocks forever; serve_once carries the coverage
    consumer: RequestConsumer,
    bus: MessageBus,
    *,
    poll_interval: int = _DEFAULT_POLL_INTERVAL,
) -> None:
    """Serve forever: dispatch all pending requests, then sleep when idle."""
    while True:
        if serve_once(consumer, bus) == 0:
            time.sleep(poll_interval)
