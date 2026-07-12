"""Azure REST reader retry tests — one transient failure self-heals.

Agent: surfaces
Role: prove a single management-API blip is retried once and only once.
External I/O: none; senders are fakes.
"""

from __future__ import annotations

import pytest

import surfaces.dashboard.azure_rest as azure_rest
from surfaces.dashboard.azure_port import AzureReadError
from surfaces.tests.test_dashboard_azure_rest import FakeSend, _settings


class FlakySend(FakeSend):
    """FakeSend that fails the first ``failures`` sends like a throttled API."""

    def __init__(self, failures: int) -> None:
        super().__init__()
        self.remaining = failures

    def __call__(
        self, method: str, url: str, scope: str, body: object
    ) -> dict[str, object]:
        if self.remaining > 0:
            self.remaining -= 1
            self.calls.append((method, url, scope, body))
            raise AzureReadError("Azure read failed (429)")
        return super().__call__(method, url, scope, body)


def test_reader_retries_one_transient_failure() -> None:
    sender = FlakySend(1)
    reader = azure_rest.AzureRestReader(_settings(), send=sender, clock=lambda: 10.0)

    rows = reader.list_job_executions("dispatcher-cron")

    assert rows
    assert len(sender.calls) == 2


def test_reader_raises_when_failure_persists_past_one_retry() -> None:
    sender = FlakySend(2)
    reader = azure_rest.AzureRestReader(_settings(), send=sender, clock=lambda: 10.0)

    with pytest.raises(AzureReadError):
        reader.list_job_executions("dispatcher-cron")

    assert len(sender.calls) == 2
