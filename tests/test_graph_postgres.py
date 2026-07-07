"""PostgresGraphStore tests with a fake connection and optional live integration."""

from __future__ import annotations

import contextlib
import os
import uuid

import pytest
from tests.graph_postgres_fakes import (
    FakePostgresConnection,
    connectable,
)
from tests.graph_postgres_fakes import (
    store as fake_store,
)

from kernel import CollectingFaultSink, Node, PostgresGraphSettings, PostgresGraphStore
from kernel.graph_postgres_queries import json_props


def test_postgres_store_uses_connection_shape_with_fake_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, fake_connection = fake_store(monkeypatch)

    parent = store.merge_node("Artifact", "parent", {"status": "new"})
    replayed = store.merge_node("Artifact", "parent", {"status": "new"})
    updated = store.merge_node("Artifact", "parent", {"status": "new", "score": 2})
    child = store.merge_node("Artifact", "child", {})
    store.add_edge(updated, child, "DERIVED", {"run": "unit"})
    store.add_edge(updated, child, "DERIVED", {"run": "replayed"})
    store.add_edge(updated, child, "ANNOTATED")

    assert replayed == parent
    assert dict(updated.props) == {"status": "new", "score": 2}
    assert store.get_node("Artifact", "missing") is None
    assert store.get_node("Artifact", "parent") == updated
    assert store.list_nodes("Missing") == ()
    assert store.list_nodes("Artifact") == (child, updated)
    assert [node.key for node in store.ancestors(child, max_depth=1)] == ["parent"]
    assert [node.key for node in store.descendants(parent, max_depth=1)] == ["child"]
    assert [
        node.key
        for node in store.descendants(parent, max_depth=1, edge_types={"DERIVED"})
    ] == ["child"]
    assert list(store.ancestors(child, max_depth=0)) == []
    assert list(store.ancestors(child, max_depth=1, edge_types={"OTHER"})) == []
    assert fake_connection.edges[0][3] == {"run": "unit"}
    store.close()
    assert fake_connection.closed


def test_postgres_store_records_faults_from_driver_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, _fake_connection = fake_store(monkeypatch)
    parent = store.merge_node("Artifact", "parent", {})

    with pytest.raises(KeyError):
        store.add_edge(parent, Node("Artifact", "missing"), "DERIVED")
    assert len(store.sink.faults) == 1
    assert store.sink.faults[0].source_module == "kernel.graph"


def test_postgres_store_rejects_schema_and_prop_overwrites(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_connection = FakePostgresConnection()
    sink = CollectingFaultSink()
    store = PostgresGraphStore(
        PostgresGraphSettings(postgres_dsn="postgresql://fake/db"),
        sink,
        connection=fake_connection,
    )
    store.merge_node("Artifact", "parent", {"status": "new"})

    with pytest.raises(ValueError, match="schema_version"):
        store.merge_node("Artifact", "parent", {"status": "new"}, schema_version=2)
    with pytest.raises(ValueError, match="cannot be overwritten"):
        store.merge_node("Artifact", "parent", {"status": "changed"})
    with pytest.raises(ValueError, match="positive"):
        store.merge_node("Artifact", "bad", {}, schema_version=0)
    assert [fault.source_module for fault in sink.faults] == [
        "kernel.graph",
        "kernel.graph",
        "kernel.graph",
    ]


def test_postgres_store_raises_when_merge_conflict_has_no_current(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, fake_connection = fake_store(monkeypatch)
    fake_connection.drop_next_merge = True

    with pytest.raises(LookupError, match="merge returned no rows"):
        store.merge_node("Artifact", "ghost", {})

    store.merge_node("Artifact", "current", {"status": "new"})
    fake_connection.drop_next_merge = True
    with pytest.raises(LookupError, match="merge returned no rows"):
        store.merge_node("Artifact", "current", {"status": "new"})


def test_postgres_store_connects_with_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_connection = connectable(monkeypatch)

    store = PostgresGraphStore(
        PostgresGraphSettings(
            postgres_dsn="postgresql://fake/db",
            postgres_connect_timeout_seconds=12,
        )
    )

    assert fake_connection.connect_args is not None
    args, kwargs = fake_connection.connect_args
    assert args == ("postgresql://fake/db",)
    assert kwargs["autocommit"] is True
    assert kwargs["connect_timeout"] == 12
    assert "row_factory" in kwargs
    store.close()


def test_postgres_json_props_normalizes_nested_values() -> None:
    props = json_props(
        {"items": ("AAPL", "MSFT"), "nested": {"scores": frozenset({2, 1})}}
    )

    assert props == {"items": ["AAPL", "MSFT"], "nested": {"scores": [1, 2]}}


@pytest.mark.integration
def test_postgres_graph_store_round_trip_when_configured() -> None:
    dsn = os.getenv("POSTGRES_TEST_DSN")
    if not dsn:
        pytest.skip("POSTGRES_TEST_DSN is not set")

    import psycopg

    suffix = uuid.uuid4().hex
    prefix = f"pgtest-{suffix}"
    parent_key = f"{prefix}-parent"
    child_key = f"{prefix}-child"
    settings = PostgresGraphSettings(
        postgres_dsn=dsn,
        postgres_connect_timeout_seconds=30,
    )
    store: PostgresGraphStore | None = None
    try:
        store = PostgresGraphStore(settings)
        parent = store.merge_node(
            "GraphStoreTest",
            parent_key,
            {"run": suffix, "snapshot": {"nested": [1, 2]}},
        )
        child = store.merge_node("GraphStoreTest", child_key, {"run": suffix})
        store.add_edge(parent, child, "DERIVED", {"run": suffix})

        assert store.get_node("GraphStoreTest", parent_key) == parent
        assert parent in store.list_nodes("GraphStoreTest")
        assert [node.key for node in store.ancestors(child, max_depth=1)] == [
            parent_key
        ]
    except psycopg.OperationalError as exc:
        pytest.skip(f"PostgreSQL not reachable (paused/offline): {exc}")
    finally:
        if store is not None:
            store.close()
        with (
            contextlib.suppress(psycopg.Error),
            psycopg.connect(dsn, connect_timeout=10, autocommit=True) as conn,
            conn.cursor() as cursor,
        ):
            pattern = f"{prefix}%"
            cursor.execute(
                "DELETE FROM edges WHERE parent_key LIKE %s OR child_key LIKE %s",
                (pattern, pattern),
            )
            cursor.execute(
                "DELETE FROM nodes WHERE key LIKE %s",
                (pattern,),
            )
