"""PostgreSQL vault probe helper tests.

Agent: orchestration
Role: verify the Key Vault seeder's Postgres probe uses psycopg safely.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from orchestration.packs import trading_vault_postgres as postgres_probe

if TYPE_CHECKING:
    import pytest


class _Cursor:
    def __enter__(self) -> _Cursor:
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def execute(self, query: str) -> None:
        self.query = query

    def fetchone(self) -> tuple[int]:
        return (1,)


class _Connection:
    def __enter__(self) -> _Connection:
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def cursor(self) -> _Cursor:
        return _Cursor()


def test_postgres_ready_runs_select_one_with_minimum_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: dict[str, object] = {}

    def connect(dsn: str, *, connect_timeout: int) -> _Connection:
        calls["dsn"] = dsn
        calls["connect_timeout"] = connect_timeout
        return _Connection()

    monkeypatch.setattr(
        "orchestration.packs.trading_vault_postgres.psycopg.connect", connect
    )

    ok = postgres_probe.postgres_ready(
        {
            "POSTGRES_DSN": "postgresql://example.invalid/db",
            "POSTGRES_CONNECT_TIMEOUT_SECONDS": "3",
        }
    )

    assert ok is True
    assert calls == {
        "dsn": "postgresql://example.invalid/db",
        "connect_timeout": 10,
    }
