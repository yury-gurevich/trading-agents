"""Tests for env-selected served-agent transport composition.

Agent: kernel
Role: pin the local fallback and Azure Service Bus request-topic composition.
External I/O: none.
"""

from __future__ import annotations

from kernel import (
    AzureServiceBusRequestConsumer,
    AzureServiceBusSettings,
    InMemoryGraphStore,
)
from kernel.serve_loop import LocalRequestConsumer
from kernel.serve_transport import consumer_from_env, request_topic


def _settings(connection_string: str | None) -> AzureServiceBusSettings:
    return AzureServiceBusSettings(
        _env_file=None,
        connection_string=connection_string,
    )


def test_consumer_from_env_uses_local_inbox_without_servicebus() -> None:
    graph = InMemoryGraphStore()

    consumer = consumer_from_env(
        "forecaster",
        graph,
        settings=_settings(None),
    )

    assert isinstance(consumer, LocalRequestConsumer)
    assert consumer.poll() == []


def test_consumer_from_env_uses_servicebus_topic_when_configured() -> None:
    graph = InMemoryGraphStore()

    consumer = consumer_from_env(
        "forecaster",
        graph,
        settings=_settings(
            "Endpoint=sb://example/;SharedAccessKeyName=x;SharedAccessKey=y"
        ),
    )

    assert isinstance(consumer, AzureServiceBusRequestConsumer)
    assert consumer._topic == "forecaster.requests"
    assert consumer._subscription_name == "agent"


def test_request_topic_names_agent_inbox_topic() -> None:
    assert request_topic("operator") == "operator.requests"
