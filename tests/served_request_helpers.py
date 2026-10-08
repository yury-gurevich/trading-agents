"""Offline served-request fixtures for S256.

Agent: kernel
Role: observe settlement, handling and publication with an expiring fake lock.
External I/O: none.
"""

from __future__ import annotations

from tests.bus_azure_receiver_helpers import (
    FailingPublishBus,
    FakeReceiver,
    RawMessage,
    raw_ready,
    request,
)

from kernel import (
    AzureServiceBusBus,
    AzureServiceBusRequestConsumer,
    AzureServiceBusSettings,
    InMemoryGraphStore,
    InProcessBus,
)


class LockLostError(Exception):
    """Synthetic message-lock expiry; no real clock or Service Bus."""


class RecordingReceiver(FakeReceiver):
    """Expire the lock on take or once a handler starts, when requested."""

    def __init__(self, messages: list[RawMessage], events: list[str]) -> None:
        super().__init__(messages)
        self.events = events
        self.fail_take = False
        self.expire_after_handling = False

    def complete_message(self, message: RawMessage) -> None:
        if self.fail_take or (self.expire_after_handling and "handled" in self.events):
            raise LockLostError("message lock expired")
        self.events.append("settled")
        super().complete_message(message)


def scene(
    refs: tuple[str, ...],
    *,
    publish_fails: bool = False,
    settings: AzureServiceBusSettings | None = None,
) -> tuple[AzureServiceBusRequestConsumer, InProcessBus, RecordingReceiver, list[str]]:
    """Use unmodified settings defaults unless an explicit override is supplied."""
    resolved = settings or AzureServiceBusSettings(
        _env_file=None, connection_string=None
    )
    events: list[str] = []
    graph = InMemoryGraphStore()
    setup = AzureServiceBusBus(settings=resolved)
    receiver = RecordingReceiver(
        [raw_ready(graph, setup, request(ref)) for ref in refs], events
    )
    reply_bus = AzureServiceBusBus(settings=resolved)
    reply_bus.subscribe("operator.reply", lambda event: events.append("published"))
    consumer = AzureServiceBusRequestConsumer(
        FailingPublishBus() if publish_fails else reply_bus,
        graph,
        topic="echo.requests",
        subscription_name="echo",
        settings=resolved,
        receiver=receiver,
    )
    served = InProcessBus()

    def handler(payload: dict[str, object]) -> dict[str, object]:
        events.extend(("handled", str(payload["ref"])))
        return {"ref": payload["ref"], "ok": True}

    served.register("echo", "echo", handler)
    return consumer, served, receiver, events
