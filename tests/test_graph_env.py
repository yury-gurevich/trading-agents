"""Tests for kernel.graph_env.build_graph_from_env."""

from __future__ import annotations

import pytest
from tests.graph_postgres_fakes import connectable

from kernel import InMemoryGraphStore, PostgresGraphStore
from kernel.graph_env import build_graph_from_env


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


def test_build_graph_from_env_neo4j_uri_gets_adr0014_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("POSTGRES_DSN", raising=False)
    monkeypatch.setenv("NEO4J_URI", "bolt://fake:7687")

    with pytest.raises(RuntimeError, match="ADR-0014"):
        build_graph_from_env()
