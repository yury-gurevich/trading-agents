"""Alpaca HTTP error formatting tests.

Agent: execution
Role: keep broker refusal details observable.
External I/O: none.
"""

from __future__ import annotations

import urllib.error
from email.message import Message
from io import BytesIO

from agents.execution import alpaca


class _UnreadableBody(BytesIO):
    def read(self, *_args: object, **_kwargs: object) -> bytes:
        raise OSError("closed body")


def test_http_error_message_falls_back_when_body_is_empty() -> None:
    """EXEC-OBS-02: empty broker refusals still surface as errors."""
    error = urllib.error.HTTPError(
        "https://alpaca.test/v2/orders", 403, "Forbidden", Message(), BytesIO()
    )

    assert alpaca._http_error_message(error) == ("HTTP Error 403: Forbidden")


def test_http_error_body_tolerates_unreadable_response() -> None:
    """EXEC-FAIL-01: broker error formatting does not raise a second error."""
    error = urllib.error.HTTPError(
        "https://alpaca.test/v2/orders",
        403,
        "Forbidden",
        Message(),
        _UnreadableBody(),
    )

    assert alpaca._http_error_body(error) == ""
