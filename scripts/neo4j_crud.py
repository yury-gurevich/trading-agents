"""Simple Neo4j CRUD demo using the project's Neo4jGraphStore.

Agent: tooling
Role: demonstrate create / read / update / delete operations against Neo4j.
External I/O: Neo4j database.

Usage:
    uv run python scripts/neo4j_crud.py

Connection settings are read from the environment (NEO4J_URI, NEO4J_USER,
NEO4J_PASSWORD, NEO4J_DATABASE) or fall back to the defaults in GraphSettings
(bolt://localhost:7687 / neo4j / no-password / neo4j).

Note on the GraphStore protocol
--------------------------------
merge_node is *append-only per property*: you can add new props to an existing
node but cannot overwrite a prop that already has a value. This is intentional
(provenance — every fact is immutable once written). For a true overwrite or
delete, drive the Neo4j session directly with Cypher, as shown in _update and
_delete below.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from kernel import Neo4jGraphStore  # noqa: E402

LABEL = "Demo"


def _sep(title: str) -> None:
    print(f"\n-- {title} {'-' * (50 - len(title))}")


def _cypher(store: Neo4jGraphStore, query: str, **params: object) -> list[object]:
    rows, _, _ = store._driver.execute_query(query, database_=store._database, **params)
    return list(rows)


def main() -> None:
    key = f"demo:crud:{datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}"
    store = Neo4jGraphStore()
    try:
        _create(store, key)
        _read(store, key)
        _update(store, key)
        _read(store, key)
        _delete(store, key)
        _verify_deleted(store, key)
    finally:
        store.close()


def _create(store: Neo4jGraphStore, key: str) -> None:
    _sep("CREATE  (via merge_node)")
    node = store.merge_node(
        LABEL,
        key,
        {
            "name": "CRUD example",
            "value": 1,
            "created_at": datetime.now(UTC).isoformat(),
        },
    )
    print(f"  label={node.label!r}  key={node.key!r}")
    print(f"  props={dict(node.props)}")


def _read(store: Neo4jGraphStore, key: str) -> None:
    _sep("READ    (via get_node + list_nodes)")
    node = store.get_node(LABEL, key)
    if node is None:
        print("  Not found.")
        return
    print(f"  label={node.label!r}  key={node.key!r}")
    print(f"  props={dict(node.props)}")
    all_nodes = store.list_nodes(LABEL)
    print(f"  list_nodes('{LABEL}') -> {len(all_nodes)} node(s) with this label")


def _update(store: Neo4jGraphStore, key: str) -> None:
    _sep("UPDATE")
    # Append a new property via merge_node (append-only: adds, never overwrites).
    node = store.merge_node(LABEL, key, {"status": "updated"})
    print(f"  Appended new prop via merge_node: status={node.props['status']!r}")

    # Overwrite an existing property value via raw Cypher SET.
    _cypher(
        store,
        f"MATCH (n:{LABEL} {{key: $key}}) SET n.value = $val",
        key=key,
        val=99,
    )
    print("  Overwrote value -> 99 via Cypher SET")


def _delete(store: Neo4jGraphStore, key: str) -> None:
    _sep("DELETE  (via Cypher; GraphStore is append-only)")
    _cypher(store, f"MATCH (n:{LABEL} {{key: $key}}) DETACH DELETE n", key=key)
    print(f"  Deleted key={key!r}")


def _verify_deleted(store: Neo4jGraphStore, key: str) -> None:
    _sep("VERIFY")
    node = store.get_node(LABEL, key)
    status = "confirmed deleted" if node is None else f"STILL PRESENT: {node}"
    print(f"  get_node after delete -> {status}")
    print()


if __name__ == "__main__":
    main()
