"""Live reads for the fleet credential-delivery audit.

Agent: tooling
Role: read delivered secrets and probe each role, returning verdicts not secrets.
External I/O: Azure CLI subprocesses and one PostgreSQL connection per target.
"""

from __future__ import annotations

from typing import Protocol

from scripts.cred_audit_plan import (
    TargetAudit,
    classify,
    container_name,
    role_of_dsn,
)
from scripts.pg_role_plan import TABLE_PRIVILEGES, TABLES
from scripts.sb_sas_cli import az_cli

APP_SECRET = "postgres-dsn"  # noqa: S105 # pragma: allowlist secret - a name.
BUS_ENV = "AZURE_SERVICEBUS_CONNECTION_STRING"
PROBE_TIMEOUT_SECONDS = 15


class _Cursor(Protocol):
    """The read-only cursor surface this audit needs."""

    def execute(self, query: str) -> object:
        """Run one read-only statement."""

    def fetchone(self) -> tuple[object, ...] | None:
        """Return the single result row."""


def delivered_dsn(target: str, resource_group: str) -> str:
    """Return the DSN a target is actually delivered. Never log this value."""
    name = container_name(target)
    scope = ["job"] if target == "dispatcher" else []
    args = [
        "containerapp",
        *scope,
        "secret",
        "show",
        "--name",
        name,
        "--resource-group",
        resource_group,
        "--secret-name",
        APP_SECRET,
        "--query",
        "value",
        "-o",
        "tsv",
    ]
    try:
        return az_cli(args, capture=True).strip()
    except (RuntimeError, OSError):
        return ""


def bus_secret_ref(target: str, resource_group: str) -> str:
    """Return the Service Bus secretRef name a target carries, or empty."""
    name = container_name(target)
    scope = ["job"] if target == "dispatcher" else []
    query = f"properties.template.containers[0].env[?name=='{BUS_ENV}'].secretRef | [0]"
    args = [
        "containerapp",
        *scope,
        "show",
        "--name",
        name,
        "--resource-group",
        resource_group,
        "--query",
        query,
        "-o",
        "tsv",
    ]
    try:
        return az_cli(args, capture=True).strip()
    except (RuntimeError, OSError):
        return ""


def probe(dsn: str) -> tuple[bool, tuple[str, ...], str]:
    """Connect as *dsn* and report reachability and granted privileges."""
    if not dsn:
        return False, (), "no DSN delivered"
    try:
        import psycopg

        with (
            psycopg.connect(dsn, connect_timeout=PROBE_TIMEOUT_SECONDS) as conn,
            conn.cursor() as cur,
        ):
            return True, _privileges(cur), ""
    except Exception as exc:
        return False, (), type(exc).__name__


def audit_target(target: str, resource_group: str) -> TargetAudit:
    """Audit one target end to end, returning a secret-free verdict."""
    dsn = delivered_dsn(target, resource_group)
    role = role_of_dsn(dsn)
    reachable, privileges, note = probe(dsn)
    return classify(
        target,
        role,
        reachable=reachable,
        privileges=privileges,
        note=note,
    )


def _privileges(cursor: _Cursor) -> tuple[str, ...]:
    """Return the granted table privileges as `table:PRIVILEGE` strings."""
    checks = [(table, priv) for table in TABLES for priv in TABLE_PRIVILEGES]
    sql = "select " + ", ".join(
        f"has_table_privilege('{table}', '{priv}')" for table, priv in checks
    )
    cursor.execute(sql)
    row = cursor.fetchone() or ()
    return tuple(
        f"{table}:{priv}"
        for (table, priv), granted in zip(checks, row, strict=False)
        if granted
    )
