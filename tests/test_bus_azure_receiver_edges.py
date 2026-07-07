"""Azure Service Bus receiver edge coverage.

Agent: kernel
Role: cover factory and no-pending reply branches for the receiver.
External I/O: none.
"""

from __future__ import annotations

from tests.bus_azure_receiver_helpers import FailingPublishBus, settings

from kernel import (
    AgentMessage,
    AzureServiceBusBus,
    AzureServiceBusRequestConsumer,
    InMemoryGraphStore,
)


def test_bus_request_consumer_factory_uses_settings_default_subscription() -> None:
    bus = AzureServiceBusBus(settings=settings(subscription_name="echo-worker"))

    consumer = bus.request_consumer(InMemoryGraphStore(), topic="echo.requests")

    assert isinstance(consumer, AzureServiceBusRequestConsumer)
    assert consumer.poll() == []


def test_reply_publish_failure_without_pending_source_does_not_raise() -> None:
    consumer = AzureServiceBusRequestConsumer(
        FailingPublishBus(),
        InMemoryGraphStore(),
        topic="echo.requests",
        subscription_name="echo",
        settings=settings(),
    )
    notice = AgentMessage(
        sender="echo",
        recipient="operator",
        message_type="notification",
        capability="echo",
        payload={"ok": True},
    )

    consumer.reply(notice)
