"""Live check for the Azure Service Bus request receiver.

Agent: tooling
Role: create disposable Service Bus topics, serve one claim-checked request through
      AzureServiceBusRequestConsumer, read the reply ready event, and tear down.
External I/O: Azure Service Bus and .env configuration.
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from kernel import (  # noqa: E402
    AgentMessage,
    AzureServiceBusBus,
    AzureServiceBusRequestConsumer,
    AzureServiceBusSettings,
    InMemoryGraphStore,
    InProcessBus,
    claim_check_read,
    claim_check_write,
)
from kernel.serve_loop import serve_once  # noqa: E402


def _connection_string(settings: AzureServiceBusSettings) -> str:
    if settings.connection_string is None:
        raise SystemExit(
            "SERVICEBUS_CONNECTION_STRING or "
            "AZURE_SERVICEBUS_CONNECTION_STRING is required"
        )
    return settings.connection_string


def _request(run_id: str) -> AgentMessage:
    return AgentMessage(
        sender="operator",
        recipient="echo",
        message_type="request",
        capability="echo",
        payload={"run_id": run_id, "probe": "servicebus-receiver"},
    )


def _served_bus() -> InProcessBus:
    bus = InProcessBus()
    bus.register(
        "echo",
        "echo",
        lambda payload: {"run_id": payload["run_id"], "served": True},
    )
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
        if not messages:
            raise RuntimeError("no reply ready event received")
        raw = messages[0]
        receiver.complete_message(raw)
        return json.loads(str(raw))


def _delete_topic(admin: object, topic: str) -> bool:
    try:
        admin.delete_topic(topic)
    except Exception as exc:
        if exc.__class__.__name__ == "ResourceNotFoundError":
            return False
        raise
    else:
        return True


def run_check() -> dict[str, Any]:
    """Run the live receiver smoke and return printable evidence."""
    from azure.servicebus.management import ServiceBusAdministrationClient

    base_settings = AzureServiceBusSettings()
    connection_string = _connection_string(base_settings)
    run_id = f"s100-{uuid.uuid4().hex[:12]}"
    request_topic = f"{run_id}-request"
    reply_topic = f"{run_id}-reply"
    worker_subscription = "worker"
    reply_subscription = "probe"
    admin = ServiceBusAdministrationClient.from_connection_string(connection_string)
    deleted: list[str] = []

    try:
        admin.create_topic(request_topic)
        admin.create_topic(reply_topic)
        admin.create_subscription(request_topic, worker_subscription)
        admin.create_subscription(reply_topic, reply_subscription)
        settings = AzureServiceBusSettings(
            connection_string=connection_string,
            receive_max_messages=1,
            receive_timeout_seconds=10.0,
            max_delivery_count=3,
        )
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
        consumer = AzureServiceBusRequestConsumer(
            azure_bus,
            graph,
            topic=request_topic,
            subscription_name=worker_subscription,
            reply_topic=reply_topic,
            settings=settings,
        )
        served = serve_once(consumer, _served_bus())
        ready_event = _read_reply(connection_string, reply_topic, reply_subscription)
        node = claim_check_read(graph, ready_event)
        reply = AgentMessage.model_validate(dict(node.props))
        if served != 1 or reply.correlation_id != message.id:
            raise RuntimeError("Service Bus receiver parity check failed")
        return {
            "run_id": run_id,
            "request_topic": request_topic,
            "reply_topic": reply_topic,
            "served": served,
            "reply_payload": reply.payload,
            "correlation_id": str(reply.correlation_id),
        }
    finally:
        if _delete_topic(admin, request_topic):
            deleted.append(request_topic)
        if _delete_topic(admin, reply_topic):
            deleted.append(reply_topic)
        if deleted:
            print(json.dumps({"teardown": deleted}, sort_keys=True))


def main() -> None:
    """Run the live smoke and print JSON evidence without secret values."""
    print(json.dumps(run_check(), sort_keys=True))


if __name__ == "__main__":
    main()
