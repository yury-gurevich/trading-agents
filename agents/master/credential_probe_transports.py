"""Default transports for master credential probes.

Agent: master
Role: provide stdlib HTTP and optional PostgreSQL probe transports.
External I/O: outbound HTTPS requests; optional PostgreSQL SELECT 1.
"""

from __future__ import annotations

import urllib.error
import urllib.request
from typing import TYPE_CHECKING

from agents.master.credential_result import (
    CheckResult,
    credential_failed,
    credential_passed,
    credential_transport_failed,
)

if TYPE_CHECKING:
    from agents.master.credential_probe_support import HttpProbeRequest


def default_http_transport(request: HttpProbeRequest) -> int:  # pragma: no cover
    """Run a declared HTTP probe with stdlib urllib."""
    req = urllib.request.Request(  # noqa: S310
        request.url, headers=request.headers, method=request.method
    )
    try:
        with urllib.request.urlopen(req, timeout=request.timeout_seconds) as resp:  # noqa: S310
            return int(resp.status)
    except urllib.error.HTTPError as exc:
        return int(exc.code)


def default_dsn_select_1(
    dsn: str, timeout_seconds: int
) -> CheckResult:  # pragma: no cover
    """Run a PostgreSQL SELECT 1 probe using psycopg when available."""
    try:
        import psycopg

        with (
            psycopg.connect(dsn, connect_timeout=timeout_seconds) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute("SELECT 1")
            row = cursor.fetchone()
        return credential_passed() if row and row[0] == 1 else credential_failed()
    except Exception as exc:  # pragma: no cover - classified with injected fakes
        sqlstate = str(getattr(exc, "sqlstate", ""))
        if sqlstate.startswith("28"):
            return credential_failed(f"postgres_sqlstate:{sqlstate}")
        return credential_transport_failed(type(exc).__name__)
