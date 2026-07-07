"""Azure Service Bus settings.

Agent: kernel
Role: hold Azure Service Bus connection settings for the AzureServiceBusBus backend.
External I/O: reads from environment variables.
"""

from __future__ import annotations

from pydantic import AliasChoices
from pydantic_settings import SettingsConfigDict

from kernel.config import AgentSettings, tunable


class AzureServiceBusSettings(AgentSettings):
    """Infrastructure settings for the Azure Service Bus message backend.

    Env vars: AZURE_SERVICEBUS_CONNECTION_STRING or SERVICEBUS_CONNECTION_STRING,
    AZURE_SERVICEBUS_NAMESPACE_ENDPOINT, AZURE_SERVICEBUS_PUBLISH_TIMEOUT_SECONDS,
    AZURE_SERVICEBUS_SUBSCRIPTION_NAME, AZURE_SERVICEBUS_RECEIVE_TIMEOUT_SECONDS,
    AZURE_SERVICEBUS_RECEIVE_MAX_MESSAGES, AZURE_SERVICEBUS_MAX_DELIVERY_COUNT, and
    AZURE_SERVICEBUS_REPLY_TOPIC_SUFFIX.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
        env_prefix="AZURE_SERVICEBUS_",
        populate_by_name=True,
    )

    connection_string: str | None = tunable(
        None,
        why="Primary connection-string credential; set in prod, absent in dev/test.",
        validation_alias=AliasChoices(
            "AZURE_SERVICEBUS_CONNECTION_STRING",
            "SERVICEBUS_CONNECTION_STRING",
        ),
    )
    namespace_endpoint: str | None = tunable(
        None,
        why="Managed-identity endpoint; used when connection_string is absent in prod.",
    )
    publish_timeout_seconds: float = tunable(
        10.0,
        why="Cap single-message send latency to avoid blocking the agent loop.",
        ge=1.0,
        le=60.0,
        unit="seconds",
    )
    subscription_name: str = tunable(
        "agent",
        why="Default subscription name for a served agent consuming a topic.",
    )
    receive_timeout_seconds: float = tunable(
        5.0,
        why="Maximum wait for a Service Bus receive poll before serve_once idles.",
        ge=0.1,
        le=60.0,
        unit="seconds",
    )
    receive_max_messages: int = tunable(
        10,
        why="Maximum request envelopes pulled from a subscription per poll pass.",
        ge=1,
        le=100,
    )
    max_delivery_count: int = tunable(
        5,
        why="Dead-letter a request after repeated decode/reply failures.",
        ge=1,
        le=100,
    )
    reply_topic_suffix: str = tunable(
        ".reply",
        why="Default requester reply topic suffix for ready-event responses.",
    )
