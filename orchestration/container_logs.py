"""Read the platform's container events and console lines from the log workspace.

Agent: orchestration
Role: query Log Analytics as the dispatcher job's managed identity (DL-301).
External I/O: HTTP GET to the job's managed-identity endpoint, HTTPS POST to the
    Log Analytics query API, both through an injectable opener.

No SDK: the image stays as it is, and the token is one documented GET. An error
carries a status word only, never a response body, a query or a token.
"""

from __future__ import annotations

import json
from datetime import UTC, timedelta
from typing import TYPE_CHECKING, Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from orchestration.container_queries import (
    REPLICA_NAME,
    ContainerLogReadError,
    events_query,
    lines_query,
    table_rows,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from datetime import datetime

    from orchestration.container_queries import Row

LOGS_API = "https://api.loganalytics.io/v1/workspaces"
_RESOURCE = "https://api.loganalytics.io"
_IDENTITY_API = "2019-08-01"
_TIMESPAN_LEAD = timedelta(hours=1)  # an event is stamped before it is ingested


class LogReader(Protocol):
    """The two reads the sensor makes of the workspace."""

    def events(self, start: datetime, until: datetime) -> list[Row]:
        """Return the sensed rows that reached the workspace in ``(start, until]``."""
        ...  # pragma: no cover - protocol declaration only.

    def error_lines(
        self, replicas: Sequence[str], start: datetime, until: datetime
    ) -> list[Row]:
        """Return candidate stderr lines of ``replicas`` stamped in the window."""
        ...  # pragma: no cover - protocol declaration only.


class LogAnalyticsReader:
    """The workspace, read as the managed identity the platform gives the job."""

    def __init__(
        self,
        workspace_id: str,
        *,
        environ: Mapping[str, str],
        timeout: float,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        """Bind the workspace, the identity endpoint's env and the opener."""
        self._workspace = workspace_id
        self._environ = environ
        self._timeout = timeout
        self._opener = opener
        self._token = ""

    def events(self, start: datetime, until: datetime) -> list[Row]:
        """Return the sensed rows that reached the workspace in ``(start, until]``."""
        return self._query(events_query(start, until), start - _TIMESPAN_LEAD, until)

    def error_lines(
        self, replicas: Sequence[str], start: datetime, until: datetime
    ) -> list[Row]:
        """Return candidate stderr lines of ``replicas``; an odd name is never sent."""
        names = sorted({name for name in replicas if REPLICA_NAME.match(name)})
        if not names:
            return []
        return self._query(lines_query(names, start, until), start, until)

    def _query(self, query: str, start: datetime, until: datetime) -> list[Row]:
        span = (
            f"{start.astimezone(UTC).isoformat()}/{until.astimezone(UTC).isoformat()}"
        )
        request = Request(  # noqa: S310 - a fixed HTTPS origin.
            f"{LOGS_API}/{quote(self._workspace, safe='')}/query",
            data=json.dumps({"query": query, "timespan": span}).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._bearer()}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        return table_rows(self._send(request))

    def _bearer(self) -> str:
        if self._token:
            return self._token
        endpoint = self._environ.get("IDENTITY_ENDPOINT", "")
        header = self._environ.get("IDENTITY_HEADER", "")
        if not endpoint or not header:
            raise ContainerLogReadError("no managed identity")
        query = urlencode({"resource": _RESOURCE, "api-version": _IDENTITY_API})
        request = Request(  # noqa: S310 - the platform's own identity endpoint.
            f"{endpoint}?{query}", headers={"X-IDENTITY-HEADER": header}, method="GET"
        )
        token = self._send(request).get("access_token")
        if not isinstance(token, str) or not token:
            raise ContainerLogReadError("no token")
        self._token = token
        return token

    def _send(self, request: Request) -> dict[str, object]:
        try:
            with self._opener(request, timeout=self._timeout) as response:
                payload = json.load(response)
        except HTTPError as exc:
            raise ContainerLogReadError(str(exc.code)) from None
        except (URLError, TimeoutError, OSError, ValueError):
            raise ContainerLogReadError("transport") from None
        if not isinstance(payload, dict):
            raise ContainerLogReadError("shape")
        return payload
