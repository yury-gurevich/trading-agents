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
_REPLY_TOPIC_SUFFIX = ".reply"
DELIBERATOR_MANAGER_TYPE = "deliberator-manager"
DELIBERATOR_PEER_AGENT_TYPES = (
    "deliberator-proponent",
    "deliberator-opponent",
)
DELIBERATOR_REPLY_AGENT_TYPES = (DELIBERATOR_MANAGER_TYPE,)
SERVED_AGENT_TYPES = (
    "curator",
    *DELIBERATOR_PEER_AGENT_TYPES,
    "forecaster",
    "operator",
    "researcher",
    "supervisor",
)


def request_topic(agent_type: str) -> str:
    """Return the Service Bus request topic for a served agent type."""
    return f"{agent_type}{_REQUEST_TOPIC_SUFFIX}"


def reply_topic(agent_type: str, suffix: str = _REPLY_TOPIC_SUFFIX) -> str:
    """Return the Service Bus reply topic for a requesting agent type."""
    return f"{agent_type}{suffix}"


def image_dir_for_served_agent(agent_type: str) -> str:
    """Return the source image directory for one served agent type."""
    if agent_type in DELIBERATOR_PEER_AGENT_TYPES:
        return "deliberator"
    return agent_type


def consumer_from_env(
    agent_type: str,
    graph: GraphStore,
    *,
    settings: AzureServiceBusSettings | None = None,
) -> RequestConsumer:
    """Use Service Bus when configured, otherwise keep the local empty inbox."""
    resolved = settings if settings is not None else AzureServiceBusSettings()
    topic = request_topic(agent_type)
    if resolved.connection_string_for_topic(topic) is None:
        return LocalRequestConsumer()

    from kernel.bus_azure import AzureServiceBusBus

    return AzureServiceBusBus(settings=resolved).request_consumer(
        graph,
        topic=topic,
    )
