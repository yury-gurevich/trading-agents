"""Prepare Service Bus request routes for served agents.

Agent: tooling
Role: create the request topics and worker subscriptions consumed by served
      agents before their containers enter the serve loop.
External I/O: Azure Service Bus management API; never prints secret values.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Protocol

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv  # noqa: E402

from kernel.bus_azure_config import AzureServiceBusSettings  # noqa: E402
from kernel.serve_transport import SERVED_AGENT_TYPES, request_topic  # noqa: E402


class ServiceBusAdmin(Protocol):
    """Small management API slice used to idempotently create routes."""

    def create_topic(self, topic: str) -> object: ...

    def create_subscription(self, topic: str, subscription: str) -> object: ...


def _connection_string(settings: AzureServiceBusSettings) -> str:
    if settings.connection_string is None:
        raise SystemExit(
            "SERVICEBUS_CONNECTION_STRING or "
            "AZURE_SERVICEBUS_CONNECTION_STRING is required"
        )
    return settings.connection_string


def ensure_topic(admin: ServiceBusAdmin, topic: str) -> bool:
    """Create topic if absent; return True when created."""
    try:
        admin.create_topic(topic)
    except Exception as exc:
        if exc.__class__.__name__ == "ResourceExistsError":
            return False
        raise
    return True


def ensure_subscription(admin: ServiceBusAdmin, topic: str, subscription: str) -> bool:
    """Create subscription if absent; return True when created."""
    try:
        admin.create_subscription(topic, subscription)
    except Exception as exc:
        if exc.__class__.__name__ == "ResourceExistsError":
            return False
        raise
    return True


def prepare_routes(
    admin: ServiceBusAdmin,
    *,
    subscription_name: str,
    agent_types: tuple[str, ...] = SERVED_AGENT_TYPES,
) -> dict[str, list[str]]:
    """Ensure every served agent has a request topic and subscription."""
    created_topics: list[str] = []
    created_subscriptions: list[str] = []
    for agent_type in agent_types:
        topic = request_topic(agent_type)
        if ensure_topic(admin, topic):
            created_topics.append(topic)
        if ensure_subscription(admin, topic, subscription_name):
            created_subscriptions.append(f"{topic}/{subscription_name}")
    return {
        "created_topics": created_topics,
        "created_subscriptions": created_subscriptions,
        "routes": [request_topic(agent_type) for agent_type in agent_types],
    }


def main() -> None:
    """Create live Service Bus routes and print non-secret evidence."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    load_dotenv(".env")
    settings = AzureServiceBusSettings()
    connection_string = _connection_string(settings)

    from azure.servicebus.management import ServiceBusAdministrationClient

    admin = ServiceBusAdministrationClient.from_connection_string(connection_string)
    with admin:
        result = prepare_routes(admin, subscription_name=settings.subscription_name)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
