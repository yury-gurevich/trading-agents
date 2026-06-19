"""Azure Service Bus backend tests.

Agent: kernel
Role: verify AzureServiceBusBus subscribe/publish/request/register work in dev mode
      (no Azure creds); integration tests skip without AZURE_SERVICEBUS_CONNECTION_STRING.
External I/O: azure.servicebus SDK (integration path only, skipped without creds).
"""

from __future__ import annotations

import os

import pytest

from kernel import AgentMessage, AzureServiceBusBus, AzureServiceBusSettings, CollectingFaultSink


# ── Unit tests (no Azure required) ──────────────────────────────────────────

def test_subscribe_and_publish_fan_out_in_process() -> None:
    bus = AzureServiceBusBus()
    received: list[dict[str, object]] = []
    bus.subscribe("test.topic", received.append)

    bus.publish("test.topic", {"value": 42})

    assert len(received) == 1
    assert received[0]["value"] == 42


def test_multiple_subscribers_all_receive_event() -> None:
    bus = AzureServiceBusBus()
    a: list[dict[str, object]] = []
    b: list[dict[str, object]] = []
    bus.subscribe("shared.topic", a.append)
    bus.subscribe("shared.topic", b.append)

    bus.publish("shared.topic", {"key": "val"})

    assert len(a) == 1
    assert len(b) == 1


def test_publish_to_unknown_topic_is_a_no_op() -> None:
    bus = AzureServiceBusBus()
    bus.publish("no.subscribers", {"x": 1})  # should not raise


def test_register_and_request_routes_in_process() -> None:
    bus = AzureServiceBusBus()
    bus.register("agent", "echo", lambda p: {"echoed": p.get("val")})
    msg = AgentMessage(
        sender="tester",
        recipient="agent",
        message_type="request",
        capability="echo",
        payload={"val": "hello"},
    )

    response = bus.request(msg)

    assert response.message_type == "response"
    assert response.payload["echoed"] == "hello"


def test_request_unknown_capability_returns_error() -> None:
    bus = AzureServiceBusBus()
    msg = AgentMessage(
        sender="tester",
        recipient="nobody",
        message_type="request",
        capability="noop",
        payload={},
    )

    response = bus.request(msg)

    assert response.message_type == "error"
    assert response.payload["error_type"] == "UnknownCapability"


def test_request_handler_fault_returns_error_and_records_to_sink() -> None:
    sink = CollectingFaultSink()
    bus = AzureServiceBusBus(sink=sink)

    def _boom(_p: dict[str, object]) -> dict[str, object]:
        raise RuntimeError("handler exploded")

    bus.register("agent", "boom", _boom)
    msg = AgentMessage(
        sender="tester",
        recipient="agent",
        message_type="request",
        capability="boom",
        payload={},
    )

    response = bus.request(msg)

    assert response.message_type == "error"
    assert sink.faults


def test_settings_connection_string_read_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AZURE_SERVICEBUS_CONNECTION_STRING", "Endpoint=sb://test.servicebus.windows.net/")
    settings = AzureServiceBusSettings()
    assert settings.connection_string is not None


def test_settings_defaults_to_none_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AZURE_SERVICEBUS_CONNECTION_STRING", raising=False)
    monkeypatch.delenv("AZURE_SERVICEBUS_NAMESPACE", raising=False)
    settings = AzureServiceBusSettings()
    assert settings.connection_string is None
    assert settings.namespace_endpoint is None


# ── Integration tests (skipped without Azure creds) ────────────────────────

@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("AZURE_SERVICEBUS_CONNECTION_STRING"),
    reason="AZURE_SERVICEBUS_CONNECTION_STRING is not set",
)
def test_azure_and_in_process_produce_same_pub_sub_outcome() -> None:
    """Parity test: same chain on both backends produces the same outcome."""
    from kernel import InProcessBus

    settings = AzureServiceBusSettings()

    for bus in (InProcessBus(), AzureServiceBusBus(settings=settings)):
        received: list[dict[str, object]] = []
        bus.subscribe("parity.topic", received.append)
        bus.publish("parity.topic", {"ping": True})
        assert len(received) == 1
        assert received[0]["ping"] is True
