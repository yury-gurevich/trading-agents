"""A11-A12: managed identity requests and safe transport failures.

Agent: orchestration
Role: prove one token fetch, two log queries and failure statuses without payloads.
External I/O: none; every HTTP call uses a stand-in opener.
"""

from __future__ import annotations

import json
from datetime import timedelta
from email.message import Message
from io import BytesIO, StringIO
from typing import TYPE_CHECKING
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

import pytest

from orchestration.container_queries import ContainerLogReadError
from orchestration.tests.container_reader_helpers import (
    EMPTY,
    IDENTITY,
    TOKEN,
    Opener,
    reader,
)
from orchestration.tests.container_sensor_helpers import NOW

if TYPE_CHECKING:
    from urllib.request import Request


def test_a11_one_identity_get_then_workspace_posts() -> None:
    """DSP-SEC-03: the job identity supplies one token reused for both POST queries."""
    table = {"tables": [{"columns": [{"name": "Reason_s"}], "rows": [["OOMKilled"]]}]}
    opener = Opener([{"access_token": TOKEN}, table, EMPTY])
    client = reader(opener)
    start = NOW - timedelta(hours=24)
    assert client.events(start, NOW) == [{"Reason_s": "OOMKilled"}]
    assert (
        client.error_lines(["provider-abc", "provider-abc", "master-abc"], start, NOW)
        == []
    )
    assert [request.get_method() for request, _ in opener.calls] == [
        "GET",
        "POST",
        "POST",
    ]
    identity, events, lines = [request for request, _ in opener.calls]
    address = urlsplit(identity.full_url)
    assert address._replace(query="").geturl() == IDENTITY["IDENTITY_ENDPOINT"]
    assert parse_qs(address.query) == {
        "resource": ["https://api.loganalytics.io"],
        "api-version": ["2019-08-01"],
    }
    assert dict(identity.header_items()) == {"X-identity-header": "fixture"}
    for request in (events, lines):
        assert (
            request.full_url
            == "https://api.loganalytics.io/v1/workspaces/workspace%2Fwith%20space/query"
        )
        assert dict(request.header_items()) == {
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/json",
            "Content-type": "application/json",
        }
    assert all(timeout == 20 for _, timeout in opener.calls)
    assert isinstance(events.data, bytes)
    event_body = json.loads(events.data)
    assert (
        event_body["timespan"] == "2026-10-13T21:30:00+00:00/2026-10-14T22:30:00+00:00"
    )
    assert isinstance(lines.data, bytes)
    line_body = json.loads(lines.data)
    assert line_body["timespan"] == f"{start.isoformat()}/{NOW.isoformat()}"
    assert "in ('master-abc', 'provider-abc')" in line_body["query"]


@pytest.mark.parametrize(
    "environ",
    [
        {},
        {"IDENTITY_ENDPOINT": "http://identity.test/token"},
        {"IDENTITY_HEADER": "fixture"},
    ],
)
def test_a12_missing_identity_sends_nothing(environ: dict[str, str]) -> None:
    """DSP-SEC-03 / DSP-FAIL-04: no identity is a safe failure before any HTTP call."""
    opener = Opener([])
    with pytest.raises(
        ContainerLogReadError, match=r"^read failed \(no managed identity\)$"
    ) as failed:
        reader(opener, environ=environ).events(NOW, NOW)
    assert failed.value.status == "no managed identity"
    assert opener.calls == []


@pytest.mark.parametrize(
    ("reply", "status"),
    [
        (URLError("body"), "transport"),
        (TimeoutError("body"), "transport"),
        (OSError("body"), "transport"),
        (ValueError("body"), "transport"),
        (["body"], "shape"),
        ({}, "no token"),
        ({"access_token": ""}, "no token"),
        ({"access_token": 7}, "no token"),
    ],
)
def test_a12_transport_and_identity_reply_failures(reply: object, status: str) -> None:
    """DSP-SEC-03 / DSP-FAIL-04: transport, shape and empty-token failures expose a
    word.
    """
    opener = Opener([reply])
    with pytest.raises(ContainerLogReadError) as failed:
        reader(opener).events(NOW, NOW)
    assert (str(failed.value), failed.value.status) == (
        f"read failed ({status})",
        status,
    )
    assert len(opener.calls) == 1


@pytest.mark.parametrize("token_stage", [True, False])
def test_a12_http_status_never_includes_reason_or_body(token_stage: bool) -> None:
    """DSP-SEC-03 / DSP-FAIL-04: both identity and query HTTP errors expose only 403."""
    plant = "synthetic"
    failure = HTTPError(
        "https://example.test",
        403,
        f"token={plant}",
        Message(),
        BytesIO(plant.encode()),
    )
    replies: list[object] = (
        [failure] if token_stage else [{"access_token": TOKEN}, failure]
    )
    with pytest.raises(ContainerLogReadError) as failed:
        reader(Opener(replies)).events(NOW, NOW)
    assert (str(failed.value), failed.value.status) == ("read failed (403)", "403")


def test_a12_invalid_json_is_transport() -> None:
    """DSP-SEC-03 / DSP-FAIL-04: malformed JSON cannot become a body-bearing failure."""

    def opener(_request: Request, *, timeout: float) -> StringIO:
        return StringIO("not JSON")

    from orchestration.container_logs import LogAnalyticsReader

    client = LogAnalyticsReader(
        "workspace", environ=IDENTITY, timeout=20, opener=opener
    )
    with pytest.raises(ContainerLogReadError, match=r"^read failed \(transport\)$"):
        client.events(NOW, NOW)
