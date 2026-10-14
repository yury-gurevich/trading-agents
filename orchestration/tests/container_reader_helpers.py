"""Stand-in HTTP replies for the container log reader.

Agent: orchestration
Role: inspect requests without opening a socket or fetching an identity token.
External I/O: none.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from io import StringIO
from typing import TYPE_CHECKING

from orchestration.container_logs import LogAnalyticsReader

if TYPE_CHECKING:
    from urllib.request import Request

IDENTITY = {
    "IDENTITY_ENDPOINT": "http://identity.test/token",
    "IDENTITY_HEADER": "fixture",
}
TOKEN = IDENTITY["IDENTITY_HEADER"]
EMPTY: dict[str, object] = {"tables": [{"columns": [], "rows": []}]}


@dataclass
class Opener:
    """A finite sequence of reply objects or raised failures."""

    replies: list[object]
    calls: list[tuple[Request, float]] = field(default_factory=list)

    def __call__(self, request: Request, *, timeout: float) -> StringIO:
        """Record method, URL, headers and body and return the next JSON reply."""
        self.calls.append((request, timeout))
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return StringIO(json.dumps(reply))


def reader(
    opener: Opener, *, environ: dict[str, str] | None = None
) -> LogAnalyticsReader:
    """Construct the real reader with the stand-in opener and no live coordinates."""
    return LogAnalyticsReader(
        "workspace/with space",
        environ=IDENTITY if environ is None else environ,
        timeout=20,
        opener=opener,
    )
