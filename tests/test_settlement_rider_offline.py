"""Ambient-Service-Bus-proof regression for the S262 rider.

Agent: tooling
Role: prove the explicit batch override remains offline by construction.
External I/O: none; the original settlement scene uses fake transport.
"""

import pytest
from tests.test_served_request_settlement import (
    test_receive_batch_tunable_can_still_be_raised as run_rider,
)


def test_e1_rider_ignores_ambient_bus_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DLIB-IDM-04 / DEP-BUS-05: ambient bus config cannot turn the rider live."""
    monkeypatch.setenv(
        "AZURE_SERVICEBUS_CONNECTION_STRING", "placeholder-not-a-credential"
    )
    run_rider()
