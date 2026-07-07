"""Azure Service Bus request-consumer tests.

Agent: kernel
Role: verify claim-check receive/reply parity and ack behavior without live Azure.
External I/O: none.
"""

from __future__ import annotations

import json

from tests.bus_azure_receiver_helpers import (
    FailingPublishBus,
    FakeReceiver,
    RawMessage,
    raw_ready,
    request,
    response,
    settings,
)

from kernel import (
    AgentMessage,
    AzureServiceBusBus,
    AzureServiceBusRequestConsumer,
    InMemoryGraphStore,
    InProcessBus,
    claim_check_read,
)
from kernel.serve_loop import LocalRequestConsumer, serve_once


def test_poll_resolves_claim_checked_request_and_reply_completes_source() -> None:
    graph = InMemoryGraphStore()
    bus = AzureServiceBusBus(settings=settings())
    message = request()
    raw = raw_ready(graph, bus, message)
    receiver = FakeReceiver([raw])
    consumer = AzureServiceBusRequestConsumer(
        bus,
        graph,
        topic="echo.requests",
        subscription_name="echo",
        settings=settings(),
        receiver=receiver,
    )
    ready_events: list[dict[str, object]] = []
    bus.subscribe("operator.reply", ready_events.append)
    served_bus = InProcessBus()
    served_bus.register(
        "echo", "echo", lambda payload: {"ref": payload["ref"], "ok": True}
    )
    local_consumer = LocalRequestConsumer([message])

    assert serve_once(local_consumer, served_bus) == 1
    assert serve_once(consumer, served_bus) == 1

    assert receiver.completed == [raw]
    assert receiver.abandoned == []
    assert receiver.dead_lettered == []
    node = claim_check_read(graph, ready_events[0])
    assert (
        AgentMessage.model_validate(dict(node.props)).payload
        == local_consumer.replies[0].payload
    )
    assert ready_events[0]["run_id"] == str(message.id)


def test_poll_handles_chunked_and_bytes_bodies() -> None:
    graph = InMemoryGraphStore()
    bus = AzureServiceBusBus(settings=settings())
    first = request("chunks")
    second = request("bytes")
    receiver = FakeReceiver(
        [
            raw_ready(graph, bus, first, body_style="chunks"),
            raw_ready(graph, bus, second, body_style="bytes"),
        ]
    )
    consumer = AzureServiceBusRequestConsumer(
        bus,
        graph,
        topic="echo.requests",
        subscription_name="echo",
        settings=settings(receive_max_messages=2),
        receiver=receiver,
    )

    assert consumer.poll() == [first, second]


def test_poll_abandons_bad_ready_event_before_delivery_limit() -> None:
    graph = InMemoryGraphStore()
    bus = AzureServiceBusBus(settings=settings())
    event = {"topic": "echo.requests", "label": "AgentMessage", "ref": "missing"}
    raw = RawMessage(json.dumps(event), delivery_count=1)
    receiver = FakeReceiver([raw])
    consumer = AzureServiceBusRequestConsumer(
        bus,
        graph,
        topic="echo.requests",
        subscription_name="echo",
        settings=settings(max_delivery_count=3),
        receiver=receiver,
    )

    assert consumer.poll() == []
    assert receiver.abandoned == [raw]


def test_poll_dead_letters_bad_ready_event_at_delivery_limit() -> None:
    graph = InMemoryGraphStore()
    bus = AzureServiceBusBus(settings=settings())
    raw = RawMessage(17, delivery_count=None)
    receiver = FakeReceiver([raw])
    consumer = AzureServiceBusRequestConsumer(
        bus,
        graph,
        topic="echo.requests",
        subscription_name="echo",
        settings=settings(max_delivery_count=1),
        receiver=receiver,
    )

    assert consumer.poll() == []
    assert receiver.dead_lettered == [(raw, "S100ReceiverFailure")]


def test_poll_is_empty_without_receiver_or_connection_string() -> None:
    consumer = AzureServiceBusRequestConsumer(
        AzureServiceBusBus(settings=settings()),
        InMemoryGraphStore(),
        topic="echo.requests",
        subscription_name="echo",
        settings=settings(),
    )

    assert consumer.poll() == []


def test_reply_abandons_pending_message_when_publish_fails() -> None:
    graph = InMemoryGraphStore()
    setup_bus = AzureServiceBusBus(settings=settings())
    message = request()
    raw = raw_ready(graph, setup_bus, message)
    receiver = FakeReceiver([raw])
    consumer = AzureServiceBusRequestConsumer(
        FailingPublishBus(),
        graph,
        topic="echo.requests",
        subscription_name="echo",
        settings=settings(),
        receiver=receiver,
    )

    assert consumer.poll() == [message]
    consumer.reply(response(message))

    assert receiver.abandoned == [raw]
    assert receiver.completed == []


def test_reply_without_pending_request_publishes_custom_ready_topic() -> None:
    graph = InMemoryGraphStore()
    bus = AzureServiceBusBus(settings=settings())
    ready_events: list[dict[str, object]] = []
    bus.subscribe("custom.reply", ready_events.append)
    consumer = AzureServiceBusRequestConsumer(
        bus,
        graph,
        topic="echo.requests",
        subscription_name="echo",
        settings=settings(),
        reply_topic="custom.reply",
    )
    notice = AgentMessage(
        sender="echo",
        recipient="operator",
        message_type="notification",
        capability="echo",
        payload={"ok": True},
    )

    consumer.reply(notice)

    node = claim_check_read(graph, ready_events[0])
    assert AgentMessage.model_validate(dict(node.props)) == notice
