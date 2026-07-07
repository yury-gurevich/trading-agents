"""Tests for kernel.graph_env.build_graph_from_env."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.graph_neo4j_fakes import FakeNeo4jDriver
from tests.graph_postgres_fakes import connectable

from kernel import InMemoryGraphStore, Neo4jGraphStore, PostgresGraphStore
from kernel.graph_env import build_graph_from_env

if TYPE_CHECKING:
    import pytest


def test_build_graph_from_env_no_uri_returns_in_memory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("POSTGRES_DSN", raising=False)
    monkeypatch.delenv("NEO4J_URI", raising=False)
    store = build_graph_from_env()
    assert isinstance(store, InMemoryGraphStore)


def test_build_graph_from_env_blank_uri_returns_in_memory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("POSTGRES_DSN", raising=False)
    monkeypatch.setenv("NEO4J_URI", "")
    store = build_graph_from_env()
    assert isinstance(store, InMemoryGraphStore)


def test_build_graph_from_env_postgres_wins_over_neo4j(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_connection = connectable(monkeypatch)
    monkeypatch.setenv("POSTGRES_DSN", "postgresql://fake/db")
    monkeypatch.setenv("NEO4J_URI", "bolt://fake:7687")

    store = build_graph_from_env()

    assert isinstance(store, PostgresGraphStore)
    assert fake_connection.connect_args is not None
    store.close()


def test_build_graph_from_env_neo4j_uri_still_returns_neo4j(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import kernel.graph_neo4j as graph_neo4j

    fake_driver = FakeNeo4jDriver()
    monkeypatch.delenv("POSTGRES_DSN", raising=False)
    monkeypatch.setenv("NEO4J_URI", "bolt://fake:7687")
    monkeypatch.setattr(
        graph_neo4j.GraphDatabase, "driver", lambda *_args, **_kwargs: fake_driver
    )

    store = build_graph_from_env()

    assert isinstance(store, Neo4jGraphStore)
    store.close()
    assert fake_driver.closed
