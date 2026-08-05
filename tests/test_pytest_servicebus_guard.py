"""Pytest Service Bus send-boundary guard tests.

Agent: kernel
Role: prove local pytest cannot publish to Azure Service Bus by accident.
External I/O: none.
"""

from __future__ import annotations

import pytest
from conftest import PytestAzureServiceBusSendError, _pytest_blocked_azure_send

from kernel import AzureServiceBusBus, AzureServiceBusSettings


def _fake_live_settings() -> AzureServiceBusSettings:
    return AzureServiceBusSettings(
        connection_string=(
            "Endpoint=sb://example/;SharedAccessKeyName=fake;SharedAccessKey=fake"
        ),
        connection_strings_json=None,
    )


def test_pytest_guard_rejects_live_servicebus_send() -> None:
    """A3 / DEP-BUS-04: a resolved test send is blocked before Azure I/O."""
    topic = "deliberator-proponent.requests"
    bus = AzureServiceBusBus(settings=_fake_live_settings())

    with pytest.raises(PytestAzureServiceBusSendError) as excinfo:
        bus.publish(topic, {"run_id": "turn-1"})

    assert excinfo.value.topic == topic
    message = str(excinfo.value)
    assert topic in message
    assert "AzureServiceBusSettings(connection_string=None" in message


def test_pytest_guard_is_autouse_for_servicebus_sends() -> None:
    """A4 / DEP-BUS-04: the send-boundary patch is active in every test."""
    assert AzureServiceBusBus._azure_send is _pytest_blocked_azure_send
