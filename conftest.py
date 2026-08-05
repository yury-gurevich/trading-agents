"""Root conftest — load .env before any test so os.getenv() picks up local config.

Shell environment takes precedence over .env (override=False), so CI secrets
set as GitHub Actions env vars are never shadowed by the local file.
"""

from __future__ import annotations

from typing import Any

import pytest
from dotenv import load_dotenv

load_dotenv(override=False)


class PytestAzureServiceBusSendError(RuntimeError):
    """Raised when pytest reaches a live Azure Service Bus send boundary."""

    def __init__(self, topic: str) -> None:
        """Name the blocked topic and the local-test remedy."""
        self.topic = topic
        super().__init__(
            "pytest blocked Azure Service Bus send to "
            f"{topic!r}; inject "
            "AzureServiceBusSettings(connection_string=None, "
            "connection_strings_json=None) or use an in-process bus"
        )


def _pytest_blocked_azure_send(
    _bus: object, topic: str, _event: dict[str, Any]
) -> None:
    raise PytestAzureServiceBusSendError(topic)


@pytest.fixture(autouse=True)
def _block_azure_servicebus_sends(monkeypatch: pytest.MonkeyPatch) -> None:
    """DEP-BUS-04 / DEP-CONFIG-02: pytest may not publish to live Service Bus."""
    from kernel.bus_azure import AzureServiceBusBus

    monkeypatch.setattr(
        AzureServiceBusBus,
        "_azure_send",
        _pytest_blocked_azure_send,
    )
