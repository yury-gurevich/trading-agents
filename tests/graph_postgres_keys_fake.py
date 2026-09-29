"""Fake psycopg connection that also answers the key-and-edge queries (S242).

Agent: kernel
Role: extend the in-memory psycopg fake with the anti-join queries and a log of
      every statement and its bound parameters, so a test can read what was sent.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.graph_postgres_fakes import FakePostgresConnection, FakePostgresCursor

from kernel.graph_postgres import PostgresGraphStore
from kernel.graph_postgres_config import PostgresGraphSettings
from kernel.graph_postgres_keys import (
    KEYS_WITHOUT_INCOMING_SQL,
    KEYS_WITHOUT_OUTGOING_SQL,
)

if TYPE_CHECKING:
    import pytest
    from tests.graph_postgres_fakes import Row


class KeysFakeConnection(FakePostgresConnection):
    """The fake connection, logging each statement with its parameters."""

    def __init__(self) -> None:
        """An empty fake database with an empty statement log."""
        super().__init__()
        self.sent: list[tuple[str, tuple[object, ...]]] = []

    def cursor(self) -> KeysFakeCursor:
        """Open a cursor that knows the key-and-edge queries."""
        return KeysFakeCursor(self)


class KeysFakeCursor(FakePostgresCursor):
    """Answers the anti-join the way its SQL reads; defers everything else."""

    connection: KeysFakeConnection

    def execute(self, query: str, params: tuple[object, ...]) -> None:
        """Log the statement, then answer it."""
        self.connection.sent.append((query, params))
        if query in (KEYS_WITHOUT_OUTGOING_SQL, KEYS_WITHOUT_INCOMING_SQL):
            self.result = self._keys(query == KEYS_WITHOUT_OUTGOING_SQL, params)
        else:
            super().execute(query, params)

    def _keys(self, outgoing: bool, params: tuple[object, ...]) -> list[Row]:
        label, edge_type, bound = str(params[0]), str(params[1]), params[2]
        linked = {
            parent if outgoing else child
            for parent, child, current, _props in self.connection.edges
            if current == edge_type
        }
        rows: list[Row] = []
        for (node_label, key), row in sorted(self.connection.nodes.items()):
            props = row["props"]
            assert isinstance(props, dict)
            created_at = props.get("created_at")
            in_window = bound is None or (
                isinstance(created_at, str) and created_at >= str(bound)
            )
            if node_label == label and (label, key) not in linked and in_window:
                rows.append({"key": key})
        return rows


def keys_store(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[PostgresGraphStore, KeysFakeConnection]:
    """A PostgresGraphStore over the logging fake."""
    import kernel.graph_postgres as graph_postgres

    fake = KeysFakeConnection()
    monkeypatch.setattr(graph_postgres, "Jsonb", lambda value: value)
    graph = PostgresGraphStore(
        PostgresGraphSettings(postgres_dsn="postgresql://fake/db"),
        connection=fake,
    )
    return graph, fake
