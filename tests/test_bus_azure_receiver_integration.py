"""Live Azure Service Bus receiver parity test.

Agent: kernel
Role: prove the Service Bus RequestConsumer serves the same request as the local
      consumer when live credentials are explicitly available.
External I/O: Azure Service Bus (integration test, skipped without creds).
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Any

import pytest

from kernel import (
    AgentMessage,
    AzureServiceBusBus,
    AzureServiceBusRequestConsumer,
    AzureServiceBusSettings,
    InMemoryGraphStore,
    InProcessBus,
    claim_check_read,
    claim_check_write,
)
from kernel.serve_loop import LocalRequestConsumer, serve_once

_CONNECTION = os.getenv("AZURE_SERVICEBUS_CONNECTION_STRING") or os.getenv(
    "SERVICEBUS_CONNECTION_STRING"
)


def _settings(connection_string: str) -> AzureServiceBusSettings:
    return AzureServiceBusSettings(
        _env_file=None,
        connection_string=connection_string,
        receive_max_messages=1,
        receive_timeout_seconds=10.0,
        max_delivery_count=3,
    )


def _request(run_id: str) -> AgentMessage:
    return AgentMessage(
        sender="operator",
        recipient="echo",
        message_type="request",
        capability="echo",
        payload={"run_id": run_id},
    )


def _served_bus() -> InProcessBus:
    bus = InProcessBus()
    bus.register("echo", "echo", lambda payload: {"run_id": payload["run_id"]})
    return bus


def _read_reply(
    connection_string: str,
    topic: str,
    subscription: str,
) -> dict[str, Any]:
    from azure.servicebus import ServiceBusClient

    client = ServiceBusClient.from_connection_string(connection_string)
    with (
        client,
        client.get_subscription_receiver(
            topic_name=topic,
            subscription_name=subscription,
        ) as receiver,
    ):
        messages = receiver.receive_messages(max_message_count=1, max_wait_time=10)
        assert messages
        raw = messages[0]
        receiver.complete_message(raw)
        return json.loads(str(raw))


def _delete_topic(admin: Any, topic: str) -> None:
    try:
        admin.delete_topic(topic)
    except Exception as exc:
        if exc.__class__.__name__ != "ResourceNotFoundError":
            raise


@pytest.mark.integration
@pytest.mark.skipif(
    not _CONNECTION,
    reason="AZURE_SERVICEBUS_CONNECTION_STRING/SERVICEBUS_CONNECTION_STRING is not set",
)
def test_servicebus_receiver_matches_local_consumer_live() -> None:
    from azure.servicebus.management import ServiceBusAdministrationClient

    assert _CONNECTION is not None
    run_id = f"s100-{uuid.uuid4().hex[:12]}"
    request_topic = f"{run_id}-request"
    reply_topic = f"{run_id}-reply"
    worker_subscription = "worker"
    reply_subscription = "probe"
    admin = ServiceBusAdministrationClient.from_connection_string(_CONNECTION)

    try:
        admin.create_topic(request_topic)
        admin.create_topic(reply_topic)
        admin.create_subscription(request_topic, worker_subscription)
        admin.create_subscription(reply_topic, reply_subscription)
        settings = _settings(_CONNECTION)
        graph = InMemoryGraphStore()
        azure_bus = AzureServiceBusBus(settings=settings)
        message = _request(run_id)
        claim_check_write(
            azure_bus,
            graph,
            topic=request_topic,
            label="AgentMessage",
            ref=str(message.id),
            props=message.model_dump(mode="json"),
            run_id=run_id,
        )
        servicebus_consumer = AzureServiceBusRequestConsumer(
            azure_bus,
            graph,
            topic=request_topic,
            subscription_name=worker_subscription,
            reply_topic=reply_topic,
            settings=settings,
        )
        local_consumer = LocalRequestConsumer([message])
        served_bus = _served_bus()

        assert serve_once(local_consumer, served_bus) == 1
        assert serve_once(servicebus_consumer, served_bus) == 1

        ready_event = _read_reply(_CONNECTION, reply_topic, reply_subscription)
        node = claim_check_read(graph, ready_event)
        servicebus_reply = AgentMessage.model_validate(dict(node.props))
        assert servicebus_reply.payload == local_consumer.replies[0].payload
        assert servicebus_reply.correlation_id == message.id
    finally:
        _delete_topic(admin, request_topic)
        _delete_topic(admin, reply_topic)
