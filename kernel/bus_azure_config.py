"""Azure Service Bus settings.

Agent: kernel
Role: hold Azure Service Bus connection settings for the AzureServiceBusBus backend.
External I/O: reads from environment variables.
"""

from __future__ import annotations

from pydantic_settings import SettingsConfigDict

from kernel.config import AgentSettings, tunable


class AzureServiceBusSettings(AgentSettings):
    """Infrastructure settings for the Azure Service Bus message backend.

    Env vars: AZURE_SERVICEBUS_CONNECTION_STRING, AZURE_SERVICEBUS_NAMESPACE_ENDPOINT,
    AZURE_SERVICEBUS_PUBLISH_TIMEOUT_SECONDS.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
        env_prefix="AZURE_SERVICEBUS_",
    )

    connection_string: str | None = tunable(
        None,
        why="Primary connection-string credential; set in prod, absent in dev/test.",
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
