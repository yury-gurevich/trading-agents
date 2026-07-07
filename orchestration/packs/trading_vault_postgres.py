"""PostgreSQL probe helper for Key Vault seeding.

Agent: orchestration
Role: prove the graph spine DSN works before the seeder writes it to vault.
External I/O: PostgreSQL database.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import psycopg

from orchestration.packs.trading_vault_probe_support import required

if TYPE_CHECKING:
    from collections.abc import Mapping


def postgres_ready(env: Mapping[str, str]) -> bool:
    """Return True when the configured DSN accepts a ``SELECT 1`` probe."""
    dsn = required(env, "POSTGRES_DSN")
    timeout = max(10, int(env.get("POSTGRES_CONNECT_TIMEOUT_SECONDS", "10")))
    with (
        psycopg.connect(dsn, connect_timeout=timeout) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute("SELECT 1")
        row = cursor.fetchone()
    return bool(row and row[0] == 1)
