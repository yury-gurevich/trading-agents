"""Serve-loop transport composition selected from environment.

Agent: kernel
Role: choose the request consumer for served agents without importing optional
      cloud SDKs unless the Azure Service Bus path is actually configured.
External I/O: reads environment-backed settings; Azure I/O is owned by consumer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from kernel.bus_azure_config import AzureServiceBusSettings
from kernel.serve_loop import LocalRequestConsumer

if TYPE_CHECKING:
    from kernel.graph import GraphStore
    from kernel.serve_loop import RequestConsumer

_REQUEST_TOPIC_SUFFIX = ".requests"


def request_topic(agent_type: str) -> str:
    """Return the Service Bus request topic for a served agent type."""
    return f"{agent_type}{_REQUEST_TOPIC_SUFFIX}"


def consumer_from_env(
    agent_type: str,
    graph: GraphStore,
    *,
    settings: AzureServiceBusSettings | None = None,
) -> RequestConsumer:
    """Use Service Bus when configured, otherwise keep the local empty inbox."""
    resolved = settings if settings is not None else AzureServiceBusSettings()
    if resolved.connection_string is None:
        return LocalRequestConsumer()

    from kernel.bus_azure import AzureServiceBusBus

    return AzureServiceBusBus(settings=resolved).request_consumer(
        graph,
        topic=request_topic(agent_type),
    )
