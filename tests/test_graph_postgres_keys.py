"""The Postgres key-and-edge query: keys only, bound parameters, list order (S242 A2).

Agent: kernel
Role: prove the anti-join SQL selects no props column, sends every value as a bound
      parameter, orders exactly as list_nodes does, and - when a database is
      configured - answers like the in-memory store on a real PostgreSQL.
External I/O: PostgreSQL only when POSTGRES_TEST_DSN is set (skipped otherwise).
"""

from __future__ import annotations

import os
import re
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from tests.graph_postgres_keys_fake import keys_store

from kernel import PostgresGraphSettings, PostgresGraphStore
from kernel.graph_postgres_keys import (
    KEYS_WITHOUT_INCOMING_SQL,
    KEYS_WITHOUT_OUTGOING_SQL,
)
from kernel.graph_postgres_queries import LIST_NODES_SQL

NOW = datetime(2026, 9, 29, 23, 0, tzinfo=UTC)
QUERIES = (KEYS_WITHOUT_OUTGOING_SQL, KEYS_WITHOUT_INCOMING_SQL)


@pytest.mark.parametrize("query", QUERIES, ids=["outgoing", "incoming"])
def test_the_anti_join_selects_the_key_and_nothing_else(query: str) -> None:
    """DL-246 D1/D3: `SELECT n.key` only, one NOT EXISTS, list_nodes' own ORDER BY,
    and four positional placeholders - no value is ever formatted into the text."""
    selected = re.match(r"\s*SELECT\s+(.*?)\s+FROM\s+nodes\s+n\b", query, re.S)
    assert selected is not None
    assert selected.group(1) == "n.key"
    assert query.count("NOT EXISTS") == 1
    assert query.strip().splitlines()[-1] == "ORDER BY n.key"
    assert LIST_NODES_SQL.strip().splitlines()[-1] == "ORDER BY key"
    assert query.count("%s") == 4
    assert "{" not in query
    assert "%(" not in query
    assert 'COLLATE "C"' in query


def test_the_store_sends_values_as_parameters_and_reads_keys_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DL-246 D1-D3: label, edge and bound travel as parameters; keys come back in
    list_nodes order; the result matches the in-memory semantics."""
    graph, fake = keys_store(monkeypatch)
    for key in ("c", "a", "b"):
        graph.merge_node("Run", key, {"created_at": NOW.isoformat()})
    graph.merge_node("Run", "old", {"created_at": "2026-09-01T00:00:00+00:00"})
    done = graph.merge_node("Done", "done", {})
    graph.add_edge(graph.list_nodes("Run")[0], done, "DONE_BY")
    fake.sent.clear()

    keys = graph.keys_without_edge("Run", "DONE_BY", created_at_from=NOW)
    incoming = graph.keys_without_edge("Run", "DONE_BY", downstream=False)

    assert keys == ("b", "c")
    assert incoming == ("a", "b", "c", "old")
    (first_sql, first_params), (second_sql, second_params) = fake.sent
    assert first_sql is KEYS_WITHOUT_OUTGOING_SQL
    assert first_params == ("Run", "DONE_BY", NOW.isoformat(), NOW.isoformat())
    assert second_sql is KEYS_WITHOUT_INCOMING_SQL
    assert second_params == ("Run", "DONE_BY", None, None)
    assert "Run" not in first_sql
    assert "DONE_BY" not in first_sql


def test_a_naive_bound_is_refused_and_faulted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DL-246 D2: a zone-less instant cannot be placed in UTC, so it raises."""
    graph, _fake = keys_store(monkeypatch)

    with pytest.raises(ValueError, match="timezone-aware"):
        graph.keys_without_edge("Run", "E", created_at_from=NOW.replace(tzinfo=None))
    assert graph.sink.faults[-1].error_type == "ValueError"


@pytest.mark.integration
def test_the_anti_join_on_a_real_postgres_when_configured() -> None:
    """DL-246 D1-D3 on PostgreSQL: the SQL parses and answers like list_nodes."""
    dsn = os.getenv("POSTGRES_TEST_DSN")
    if not dsn:
        pytest.skip("POSTGRES_TEST_DSN is not set")
    import psycopg

    label = f"KeysTest{uuid.uuid4().hex}"
    store = PostgresGraphStore(PostgresGraphSettings(postgres_dsn=dsn))
    try:
        stamps = {
            "c": NOW.isoformat(),
            "a": (NOW + timedelta(microseconds=1)).isoformat(),
            "b": (NOW - timedelta(seconds=1)).isoformat(),
        }
        for key, stamp in stamps.items():
            store.merge_node(label, key, {"created_at": stamp, "blob": "x" * 64})
        store.merge_node(label, "d", {})
        done = store.merge_node(label, "done", {})
        store.add_edge(store.list_nodes(label)[0], done, "DONE_BY")
        listed = tuple(node.key for node in store.list_nodes(label))

        assert store.keys_without_edge(label, "DONE_BY") == listed[1:]
        assert store.keys_without_edge(label, "DONE_BY", created_at_from=NOW) == ("c",)
        assert store.keys_without_edge(label, "DONE_BY", downstream=False) == tuple(
            key for key in listed if key != "done"
        )
    finally:
        with psycopg.connect(dsn, autocommit=True) as conn, conn.cursor() as cursor:
            cursor.execute("DELETE FROM edges WHERE parent_label = %s", (label,))
            cursor.execute("DELETE FROM nodes WHERE label = %s", (label,))
        store.close()
