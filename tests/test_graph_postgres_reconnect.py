"""PostgresGraphStore reconnect-once behaviour for server-dropped connections."""

from __future__ import annotations

import psycopg
import pytest
from tests.graph_postgres_fakes import FakePostgresConnection

from kernel import PostgresGraphSettings, PostgresGraphStore


class DroppableConnection(FakePostgresConnection):
    """Fake connection whose next cursor() fails like a server-side drop."""

    def __init__(self) -> None:
        super().__init__()
        self.fail_next_cursor = False

    def cursor(self) -> object:
        if self.fail_next_cursor:
            self.fail_next_cursor = False
            raise psycopg.OperationalError("the connection is closed")
        return super().cursor()


def _owned_store(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[PostgresGraphStore, list[DroppableConnection]]:
    import kernel.graph_postgres as graph_postgres

    connections: list[DroppableConnection] = []

    def connect(*_args: object, **_kwargs: object) -> DroppableConnection:
        connections.append(DroppableConnection())
        return connections[-1]

    monkeypatch.setattr(graph_postgres.psycopg, "connect", connect)
    monkeypatch.setattr(graph_postgres, "Jsonb", lambda value: value)
    store = PostgresGraphStore(
        PostgresGraphSettings(postgres_dsn="postgresql://fake/db")
    )
    return store, connections


def test_owned_store_reconnects_once_when_server_dropped_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, connections = _owned_store(monkeypatch)
    connections[0].fail_next_cursor = True

    node = store.merge_node("Artifact", "survivor", {"status": "new"})

    assert node.key == "survivor"
    assert len(connections) == 2
    assert store.get_node("Artifact", "survivor") == node


def test_owned_store_raises_when_replacement_connection_also_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, connections = _owned_store(monkeypatch)
    store.merge_node("Artifact", "before", {})
    connections[0].fail_next_cursor = True

    def connect_dead(*_args: object, **_kwargs: object) -> DroppableConnection:
        dead = DroppableConnection()
        dead.fail_next_cursor = True
        connections.append(dead)
        return dead

    import kernel.graph_postgres as graph_postgres

    monkeypatch.setattr(graph_postgres.psycopg, "connect", connect_dead)
    with pytest.raises(psycopg.OperationalError, match="connection is closed"):
        store.get_node("Artifact", "before")


def test_injected_connection_is_never_replaced(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import kernel.graph_postgres as graph_postgres

    injected = DroppableConnection()
    monkeypatch.setattr(graph_postgres, "Jsonb", lambda value: value)
    store = PostgresGraphStore(
        PostgresGraphSettings(postgres_dsn="postgresql://fake/db"),
        connection=injected,
    )
    store.merge_node("Artifact", "kept", {})
    injected.fail_next_cursor = True

    with pytest.raises(psycopg.OperationalError, match="connection is closed"):
        store.get_node("Artifact", "kept")

    assert store.get_node("Artifact", "kept") is not None
