"""Controlled Service Bus SAS proof operations.

Agent: tooling
Role: prove entity-level Send/Listen, least authority, and revocation.
External I/O: Azure Service Bus; prints no keys or connection strings.
"""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Iterable

from scripts.sb_sas_live_routes import (
    PROBE_SUBSCRIPTION,
    REQUESTER_RULE,
    SERVED_RULE,
    WORKER_SUBSCRIPTION,
    connection_string,
    create_canary_routes,
    delete_rule,
    topic_command,
)

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
from kernel.serve_loop import serve_once

REVOCATION_ATTEMPTS = 4
REVOCATION_SLEEP_SECONDS = 5


def run_check(resource_group: str, namespace_name: str) -> dict[str, object]:
    """Run the canary SAS proof and return non-secret evidence."""
    run_id = f"s133-{uuid.uuid4().hex[:10]}"
    request_topic = f"{run_id}-request"
    reply_topic = f"{run_id}-reply"
    graph = InMemoryGraphStore()
    created = create_canary_routes(
        resource_group, namespace_name, request_topic, reply_topic
    )
    try:
        creds = _credentials(resource_group, namespace_name, request_topic, reply_topic)
        message = _send_request(graph, creds["requester_send"], request_topic, run_id)
        served = _serve_once(
            graph,
            creds["served_listen"],
            creds["served_send"],
            request_topic,
            reply_topic,
        )
        reply = _read_reply(graph, creds["requester_listen"], reply_topic)
        least_authority = _send_refusal(creds["requester_send"], reply_topic)
        delete_rule(resource_group, namespace_name, request_topic, REQUESTER_RULE)
        revoked = _send_refusal(creds["requester_send"], request_topic)
        return {
            "run_id": run_id,
            "positive_served": served,
            "reply_type": reply.message_type,
            "correlation_id": str(reply.correlation_id),
            "request_id": str(message.id),
            "least_authority_refusal": least_authority,
            "revocation_refusal": revoked,
            "created": created,
        }
    finally:
        topic_command("delete", resource_group, namespace_name, request_topic)
        topic_command("delete", resource_group, namespace_name, reply_topic)


def _credentials(
    resource_group: str, namespace_name: str, request_topic: str, reply_topic: str
) -> dict[str, str]:
    return {
        "requester_send": connection_string(
            resource_group, namespace_name, request_topic, REQUESTER_RULE
        ),
        "requester_listen": connection_string(
            resource_group, namespace_name, reply_topic, REQUESTER_RULE
        ),
        "served_listen": connection_string(
            resource_group, namespace_name, request_topic, SERVED_RULE
        ),
        "served_send": connection_string(
            resource_group, namespace_name, reply_topic, SERVED_RULE
        ),
    }


def _send_request(
    graph: InMemoryGraphStore, connection_string_value: str, topic: str, run_id: str
) -> AgentMessage:
    bus = _bus(connection_string_value)
    message = AgentMessage(
        sender="s133-requester",
        recipient="echo",
        message_type="request",
        capability="echo",
        payload={"run_id": run_id},
    )
    claim_check_write(
        bus,
        graph,
        topic=topic,
        label="AgentMessage",
        ref=str(message.id),
        props=message.model_dump(mode="json"),
        run_id=run_id,
    )
    return message


def _serve_once(
    graph: InMemoryGraphStore,
    listen_connection_string: str,
    send_connection_string: str,
    request_topic: str,
    reply_topic: str,
) -> int:
    consumer = AzureServiceBusRequestConsumer(
        _bus(send_connection_string),
        graph,
        topic=request_topic,
        subscription_name=WORKER_SUBSCRIPTION,
        reply_topic=reply_topic,
        settings=_settings(listen_connection_string),
    )
    return serve_once(consumer, _served_bus())


def _read_reply(
    graph: InMemoryGraphStore, connection_string_value: str, reply_topic: str
) -> AgentMessage:
    from azure.servicebus import ServiceBusClient

    client = ServiceBusClient.from_connection_string(connection_string_value)
    with (
        client,
        client.get_subscription_receiver(
            topic_name=reply_topic, subscription_name=PROBE_SUBSCRIPTION
        ) as receiver,
    ):
        messages = receiver.receive_messages(max_message_count=1, max_wait_time=20)
        if not messages:
            raise RuntimeError("no reply ready event received")
        raw = messages[0]
        receiver.complete_message(raw)
    node = claim_check_read(graph, json.loads(_body_text(raw)))
    return AgentMessage.model_validate(dict(node.props))


def _send_refusal(connection_string_value: str, topic: str) -> str:
    for _attempt in range(REVOCATION_ATTEMPTS):
        try:
            _bus(connection_string_value).publish(topic, {"probe": "s133-refusal"})
        except Exception as exc:
            return type(exc).__name__
        time.sleep(REVOCATION_SLEEP_SECONDS)
    raise RuntimeError("scoped Send unexpectedly succeeded")


def _served_bus() -> InProcessBus:
    bus = InProcessBus()
    bus.register("echo", "echo", lambda payload: {"run_id": payload["run_id"]})
    return bus


def _bus(connection_string_value: str) -> AzureServiceBusBus:
    return AzureServiceBusBus(settings=_settings(connection_string_value))


def _settings(connection_string_value: str) -> AzureServiceBusSettings:
    return AzureServiceBusSettings(
        _env_file=None, connection_string=connection_string_value
    )


def _body_text(raw: object) -> str:
    body = getattr(raw, "body", raw)
    if isinstance(body, bytes):
        return body.decode("utf-8")
    if isinstance(body, str):
        return body
    if isinstance(body, Iterable):
        return "".join(
            chunk.decode("utf-8") if isinstance(chunk, bytes) else str(chunk)
            for chunk in body
        )
    return str(body)
