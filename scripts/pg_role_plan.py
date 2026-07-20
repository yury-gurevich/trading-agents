"""Pure planning helpers for per-agent PostgreSQL roles.

Agent: tooling
Role: generate role names, SQL statements, and role DSNs without live I/O.
External I/O: none.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import quote, urlsplit, urlunsplit

AGENTS = (
    "scanner",
    "analyst",
    "portfolio_manager",
    "execution",
    "monitor",
    "reporter",
    "forecaster",
    "operator",
    "supervisor",
    "curator",
    "researcher",
    "provider",
    "master",
    "dispatcher",
    "ops",
)
CANARY = "canary"
TABLES = ("nodes", "edges")
TABLE_PRIVILEGES = ("SELECT", "INSERT", "UPDATE")
SEQUENCE_PRIVILEGES = ("USAGE", "SELECT", "UPDATE")
_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class SqlStatement:
    """SQL text plus literal parameters."""

    sql: str
    params: tuple[str, ...] = ()


def agent_role_names(*, include_canary: bool = False) -> tuple[str, ...]:
    """Return the provisioned PostgreSQL role names."""
    agents = (*AGENTS, CANARY) if include_canary else AGENTS
    return tuple(db_role(agent) for agent in agents)


def normalize_agent(raw: str, *, allow_canary: bool = False) -> str:
    """Normalize an agent or role argument into the canonical agent key."""
    value = raw.strip().lower().replace("-", "_")
    if value.startswith("ta_"):
        value = value[3:]
    allowed = set(AGENTS)
    if allow_canary:
        allowed.add(CANARY)
    if value not in allowed:
        raise ValueError(f"unknown Postgres role target: {raw}")
    return value


def db_role(agent: str) -> str:
    """Return the database role name for *agent*."""
    return f"ta_{normalize_agent(agent, allow_canary=True)}"


def key_vault_secret_name(agent: str) -> str:
    """Return the Key Vault secret name for one role DSN."""
    return f"postgres-dsn-{normalize_agent(agent, allow_canary=True).replace('_', '-')}"


def role_exists_statement(role: str) -> SqlStatement:
    """Return the role-existence probe."""
    return SqlStatement("SELECT 1 FROM pg_roles WHERE rolname = %s", (role,))


def role_plan(
    role: str, password: str, *, exists: bool, rotate: bool
) -> tuple[SqlStatement, ...]:
    """Return the SQL needed to create or rotate a role and restore grants."""
    statements: list[SqlStatement] = []
    if rotate and exists:
        statements.append(_alter_role_password_statement(role, password))
    elif not exists:
        statements.append(_create_role_statement(role, password))
    statements.extend(grant_statements(role))
    return tuple(statements)


def grant_statements(role: str) -> tuple[SqlStatement, ...]:
    """Return idempotent schema/table/default-privilege grants for *role*."""
    db_role = _quote_identifier(role)
    table_list = ", ".join(f"public.{_quote_identifier(table)}" for table in TABLES)
    table_privs = ", ".join(TABLE_PRIVILEGES)
    sequence_privs = ", ".join(SEQUENCE_PRIVILEGES)
    return (
        SqlStatement(f"GRANT USAGE ON SCHEMA public TO {db_role}"),
        SqlStatement(f"GRANT {table_privs} ON TABLE {table_list} TO {db_role}"),
        SqlStatement(
            f"GRANT {sequence_privs} ON ALL SEQUENCES IN SCHEMA public TO {db_role}"
        ),
        SqlStatement(
            "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
            f"GRANT {table_privs} ON TABLES TO {db_role}"
        ),
        SqlStatement(
            "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
            f"GRANT {sequence_privs} ON SEQUENCES TO {db_role}"
        ),
    )


def build_role_dsn(admin_dsn: str, role: str, password: str) -> str:
    """Return *admin_dsn* with userinfo replaced by the role credentials."""
    parsed = urlsplit(admin_dsn)
    if not parsed.scheme or not parsed.hostname:
        raise ValueError("POSTGRES_DSN must be a URL-style DSN")
    host = parsed.hostname
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    if parsed.port is not None:
        host = f"{host}:{parsed.port}"
    userinfo = f"{quote(role, safe='')}:{quote(password, safe='')}@"
    return urlunsplit((parsed.scheme, userinfo + host, parsed.path, parsed.query, ""))


def _create_role_statement(role: str, password: str) -> SqlStatement:
    role_sql = _quote_identifier(role)
    password_sql = _quote_literal(password)
    sql = f"CREATE ROLE {role_sql} LOGIN PASSWORD {password_sql}"
    return SqlStatement(sql)


def _alter_role_password_statement(role: str, password: str) -> SqlStatement:
    role_sql = _quote_identifier(role)
    password_sql = _quote_literal(password)
    return SqlStatement(f"ALTER ROLE {role_sql} PASSWORD {password_sql}")


def _quote_identifier(value: str) -> str:
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"unsafe SQL identifier: {value}")
    return f'"{value}"'


def _quote_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"
