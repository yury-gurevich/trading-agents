"""Provision per-agent PostgreSQL roles for the graph spine.

Agent: tooling
Role: create or rotate role identities and grants without emitting credentials.
External I/O: environment, PostgreSQL, optional Azure CLI Key Vault writes.
"""

from __future__ import annotations

import argparse
import os
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

import psycopg

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.pg_role_plan import (  # noqa: E402
    AGENTS,
    CANARY,
    SqlStatement,
    build_role_dsn,
    db_role,
    key_vault_secret_name,
    normalize_agent,
    role_exists_statement,
    role_plan,
)

ADMIN_DSN_ENV = "POSTGRES_DSN"
KEY_VAULT_ENV = "POSTGRES_ROLE_KEY_VAULT"
PASSWORD_BYTES = 32


def provision_roles(
    admin_dsn: str,
    targets: tuple[str, ...],
    *,
    rotate: str | None = None,
    key_vault_name: str = "",
) -> None:
    """Create/rotate target roles and optionally store generated DSNs in Key Vault."""
    rotate_role = db_role(rotate) if rotate else None
    with psycopg.connect(admin_dsn, autocommit=True) as conn:
        for agent in targets:
            role = db_role(agent)
            exists = _role_exists(conn, role)
            should_rotate = rotate_role == role
            password = secrets.token_urlsafe(PASSWORD_BYTES)
            for statement in role_plan(
                role, password, exists=exists, rotate=should_rotate
            ):
                _execute(conn, statement)
            if (should_rotate or not exists) and key_vault_name:
                dsn = build_role_dsn(admin_dsn, role, password)
                _set_key_vault_secret(key_vault_name, key_vault_secret_name(agent), dsn)


def main(argv: list[str] | None = None) -> int:
    """Run the provisioner and return a process exit code."""
    args = _parser().parse_args(argv)
    admin_dsn = os.environ.get(ADMIN_DSN_ENV, "")
    if not admin_dsn:
        sys.stderr.write(f"error {ADMIN_DSN_ENV} is required\n")
        return 1
    try:
        targets = _targets(args.rotate, include_canary=args.include_canary)
        key_vault = "" if args.database_only else args.key_vault_name
        if not key_vault and not args.database_only:
            sys.stderr.write(f"error {KEY_VAULT_ENV} or --key-vault-name is required\n")
            return 1
        provision_roles(
            admin_dsn, targets, rotate=args.rotate, key_vault_name=key_vault
        )
    except Exception as exc:  # keep secrets out of tracebacks and command output
        sys.stderr.write(f"error pg provisioning failed: {type(exc).__name__}\n")
        return 1
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="provision per-agent Postgres roles")
    parser.add_argument(
        "--rotate", help="agent/role to rotate, e.g. scanner or ta_scanner"
    )
    parser.add_argument("--include-canary", action="store_true")
    parser.add_argument("--database-only", action="store_true")
    parser.add_argument("--key-vault-name", default=os.environ.get(KEY_VAULT_ENV, ""))
    return parser


def _targets(rotate: str | None, *, include_canary: bool) -> tuple[str, ...]:
    if rotate:
        return (normalize_agent(rotate, allow_canary=True),)
    return (*AGENTS, CANARY) if include_canary else AGENTS


def _role_exists(conn: psycopg.Connection[object], role: str) -> bool:
    with conn.cursor() as cursor:
        statement = role_exists_statement(role)
        cursor.execute(statement.sql, statement.params)
        return cursor.fetchone() is not None


def _execute(conn: psycopg.Connection[object], statement: SqlStatement) -> None:
    with conn.cursor() as cursor:
        cursor.execute(statement.sql, statement.params)


def _set_key_vault_secret(vault_name: str, secret_name: str, value: str) -> None:
    az = shutil.which("az")
    if not az:
        raise RuntimeError("Azure CLI not found")
    subprocess.run(  # noqa: S603 - fixed Azure CLI command, no shell expansion.
        [
            az,
            "keyvault",
            "secret",
            "set",
            "--vault-name",
            vault_name,
            "--name",
            secret_name,
            "--value",
            value,
            "-o",
            "none",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


if __name__ == "__main__":
    raise SystemExit(main())
