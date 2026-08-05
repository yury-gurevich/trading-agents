"""Root conftest — load .env before any test so os.getenv() picks up local config.

Shell environment takes precedence over .env (override=False), so CI secrets
set as GitHub Actions env vars are never shadowed by the local file.
"""

from __future__ import annotations

from typing import Any

import pytest
from dotenv import load_dotenv

load_dotenv(override=False)


class PytestAzureServiceBusSendError(BaseException):
    """Raised when pytest reaches a live Azure Service Bus send boundary.

    Derives from ``BaseException``, not ``Exception``, for the same reason
    ``KeyboardInterrupt`` does: ``kernel.errors.fault_boundary`` catches bare
    ``Exception`` and, with ``reraise=False``, converts it into a ``Fault`` and
    continues. A guard that can be swallowed still blocks the send, but the test
    passes green and the author never learns the test tried to transact — and the
    code under test silently takes a degraded path it would never take in
    production. Measured before this change: the error became a ``Fault`` of type
    ``PytestAzureServiceBusSendError`` and the probe test reported ``1 passed``.
    """

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
