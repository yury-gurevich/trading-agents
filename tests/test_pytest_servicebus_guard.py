"""Pytest Service Bus send-boundary guard tests.

Agent: kernel
Role: prove local pytest cannot publish to Azure Service Bus by accident.
External I/O: none.
"""

from __future__ import annotations

import pytest
from conftest import PytestAzureServiceBusSendError, _pytest_blocked_azure_send

from kernel import AzureServiceBusBus, AzureServiceBusSettings
from kernel.errors import CollectingFaultSink, fault_boundary


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


def test_pytest_guard_is_not_swallowed_by_a_fault_boundary() -> None:
    """DEP-BUS-04: a degraded-but-continue boundary must not eat the guard.

    Plants the violation: the publish happens inside ``reraise=False``, which is
    the documented degraded-path idiom and catches bare ``Exception``. When the
    guard derived from ``RuntimeError`` this test passed with the send silently
    converted into a ``Fault`` — blocked, but invisible. The guard must escape
    the boundary and no fault may be recorded in its place.
    """
    bus = AzureServiceBusBus(settings=_fake_live_settings())
    sink = CollectingFaultSink()

    with (
        pytest.raises(PytestAzureServiceBusSendError),
        fault_boundary(sink, agent="probe", module="probe", reraise=False),
    ):
        bus.publish("deliberator-proponent.requests", {"run_id": "turn-1"})

    assert sink.faults == []
