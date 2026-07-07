"""Publish one claim-checked Service Bus request and optionally wait for a reply.

Agent: tooling
Role: provide the separate-process request side for S102 control-plane proofs.
External I/O: PostgreSQL graph store and Azure Service Bus; never prints secrets.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv  # noqa: E402

from kernel import (  # noqa: E402
    AgentMessage,
    AzureServiceBusBus,
    AzureServiceBusSettings,
    claim_check_read,
    claim_check_write,
)
from kernel.graph_env import build_graph_from_env  # noqa: E402
from kernel.serve_transport import request_topic  # noqa: E402


def _connection_string(settings: AzureServiceBusSettings) -> str:
    if settings.connection_string is None:
        raise SystemExit(
            "SERVICEBUS_CONNECTION_STRING or "
            "AZURE_SERVICEBUS_CONNECTION_STRING is required"
        )
    return settings.connection_string


def _payload(text: str) -> dict[str, Any]:
    data = json.loads(text)
    if not isinstance(data, dict):
        raise SystemExit("--payload-json must decode to a JSON object")
    return data


def _jsonable(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_jsonable(item) for item in value]
    return value


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


def _ensure_topic(admin: object, topic: str) -> None:
    try:
        admin.create_topic(topic)
    except Exception as exc:
        if exc.__class__.__name__ != "ResourceExistsError":
            raise


def _ensure_subscription(admin: object, topic: str, subscription: str) -> None:
    try:
        admin.create_subscription(topic, subscription)
    except Exception as exc:
        if exc.__class__.__name__ != "ResourceExistsError":
            raise


def _ensure_route(
    connection_string: str,
    *,
    request: str,
    worker_subscription: str,
    reply: str,
    reply_subscription: str,
) -> None:
    from azure.servicebus.management import ServiceBusAdministrationClient

    admin = ServiceBusAdministrationClient.from_connection_string(connection_string)
    with admin:
        _ensure_topic(admin, request)
        _ensure_topic(admin, reply)
        _ensure_subscription(admin, request, worker_subscription)
        _ensure_subscription(admin, reply, reply_subscription)


def _read_ready_event(
    connection_string: str,
    *,
    topic: str,
    subscription: str,
    timeout: float,
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
        messages = receiver.receive_messages(max_message_count=1, max_wait_time=timeout)
        if not messages:
            raise RuntimeError("no reply ready event received")
        raw = messages[0]
        receiver.complete_message(raw)
        return json.loads(_body_text(raw))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Service Bus served-agent request")
    parser.add_argument("--recipient", required=True, help="served agent type")
    parser.add_argument("--capability", required=True, help="capability to invoke")
    parser.add_argument("--payload-json", default="{}", help="request payload object")
    parser.add_argument("--sender", default="s102-probe", help="reply topic owner")
    parser.add_argument("--run-id", default="", help="claim-check run correlation")
    parser.add_argument("--reply-subscription", default="probe")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--ensure-route", action="store_true")
    parser.add_argument("--no-wait", action="store_true")
    return parser


def main() -> None:
    """Publish the request and print non-secret evidence as JSON."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    args = _parser().parse_args()
    load_dotenv()
    settings = AzureServiceBusSettings()
    connection_string = _connection_string(settings)
    graph = build_graph_from_env()
    bus = AzureServiceBusBus(settings=settings)
    run_id = args.run_id or f"s102-{uuid.uuid4().hex[:12]}"
    topic = request_topic(args.recipient)
    reply_topic = f"{args.sender}{settings.reply_topic_suffix}"
    if args.ensure_route:
        _ensure_route(
            connection_string,
            request=topic,
            worker_subscription=settings.subscription_name,
            reply=reply_topic,
            reply_subscription=args.reply_subscription,
        )
    message = AgentMessage(
        sender=args.sender,
        recipient=args.recipient,
        message_type="request",
        capability=args.capability,
        payload=_payload(args.payload_json),
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
    if args.no_wait:
        print(
            json.dumps(
                {"run_id": run_id, "request_id": str(message.id), "topic": topic}
            )
        )
        return
    ready = _read_ready_event(
        connection_string,
        topic=reply_topic,
        subscription=args.reply_subscription,
        timeout=args.timeout,
    )
    node = claim_check_read(graph, ready)
    reply = AgentMessage.model_validate(dict(node.props))
    print(
        json.dumps(
            {
                "run_id": run_id,
                "request_id": str(message.id),
                "topic": topic,
                "reply_topic": reply_topic,
                "reply_type": reply.message_type,
                "correlation_id": str(reply.correlation_id),
                "payload": _jsonable(reply.payload),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
