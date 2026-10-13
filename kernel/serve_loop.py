"""Serve/consume loop for RPC-triggered agent entrypoints — the pull side's twin.

Agent: kernel
Role: shared "receive a request -> dispatch to the bound handler -> reply" loop so
      every RPC-served agent entrypoint stays thin (DL-30 / DL-35). Dispatch is
      delegated to the bus's own ``request`` — reusing its capability lookup, the
      caller-authorization gate, and the fault boundary — so serving and calling
      share one code path and the loop can never die on a bad request.
      ``serve_loop`` wraps ``serve_once`` until the stop signal (twin of
      ``work_loop`` on the graph-pull side).
External I/O: none (the injected RequestConsumer owns any transport I/O).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from kernel.errors import CollectingFaultSink, fault_boundary
from kernel.stop import UNNAMED, StopSignal, closing_steps, end_loop, install

if TYPE_CHECKING:
    from kernel.bus import MessageBus
    from kernel.envelope import AgentMessage
    from kernel.errors import FaultSink
    from kernel.graph import GraphStore

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


def serve_once(
    consumer: RequestConsumer, bus: MessageBus, *, sink: FaultSink | None = None
) -> int:
    """Dispatch every pending request through the bus and reply; return the count.

    Each request is routed via ``bus.request`` — which enforces the capability
    matrix and never raises (handler faults come back as error messages) — so a
    single bad request can never kill the serving loop. Reply failures are
    recorded without retrying settled requests; receive/take failures propagate.
    """
    resolved = sink if sink is not None else CollectingFaultSink()
    requests = consumer.poll()
    for request in requests:
        response = bus.request(request)
        with fault_boundary(
            resolved,
            agent=request.recipient,
            module="kernel.serve_loop",
            capability=request.capability,
            reraise=False,
        ):
            consumer.reply(response)
    return len(requests)


def serve_loop(
    consumer: RequestConsumer,
    bus: MessageBus,
    *,
    poll_interval: int = _DEFAULT_POLL_INTERVAL,
    sink: FaultSink | None = None,
    graph: GraphStore | None = None,
    agent: str | None = None,
    stop: StopSignal | None = None,
) -> int:
    """Serve until told to stop: dispatch pending requests, sleep when idle.

    A container's main loop: it listens for the stop signal itself unless a *stop*
    is handed in. A request already taken is answered (it was settled when taken);
    then the loop flushes the sink, closes the consumer and the graph and writes
    the closing line (``kernel.stop``). Returns the number of requests served.
    """
    name = agent or UNNAMED
    stopping = stop if stop is not None else StopSignal()
    if stop is None:
        install(stopping, agent=name)
    served = 0
    while not stopping.requested:
        count = serve_once(consumer, bus, sink=sink)
        served += count
        if count == 0:
            stopping.wait(poll_interval)
    end_loop(
        stopping,
        agent=name,
        steps=closing_steps(
            faults=getattr(sink, "flush", None), requests=consumer, graph=graph
        ),
    )
    return served
