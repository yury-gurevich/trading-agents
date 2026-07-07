"""PostgreSQL SQL helpers for the graph backend.

Agent: kernel
Role: keep SQL text and JSON row conversion out of the PostgresGraphStore adapter.
External I/O: none.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from kernel.graph import Node

if TYPE_CHECKING:
    from kernel.graph_support import Props

MERGE_NODE_SQL = """
INSERT INTO nodes (label, key, props, schema_version)
VALUES (%s, %s, %s, %s)
ON CONFLICT (label, key) DO UPDATE
SET props = EXCLUDED.props || nodes.props,
    schema_version = nodes.schema_version
WHERE nodes.schema_version = EXCLUDED.schema_version
  AND NOT EXISTS (
      SELECT 1
      FROM jsonb_each(EXCLUDED.props) AS incoming(key, value)
      WHERE nodes.props ? incoming.key
        AND nodes.props -> incoming.key <> incoming.value
  )
RETURNING label, key, props, schema_version
"""

GET_NODE_SQL = """
SELECT label, key, props, schema_version
FROM nodes
WHERE label = %s AND key = %s
"""

LIST_NODES_SQL = """
SELECT label, key, props, schema_version
FROM nodes
WHERE label = %s
ORDER BY key
"""

NODE_EXISTS_SQL = """
SELECT 1
FROM nodes
WHERE label = %s AND key = %s
"""

ADD_EDGE_SQL = """
INSERT INTO edges (
    parent_label, parent_key, child_label, child_key, edge_type, props
)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (parent_label, parent_key, child_label, child_key, edge_type) DO NOTHING
"""

TRAVERSE_ANCESTORS_SQL = """
WITH RECURSIVE walk(label, key, props, schema_version, depth, path) AS (
    SELECT n.label, n.key, n.props, n.schema_version, 1,
           ARRAY[n.label || ':' || n.key]
    FROM edges e
    JOIN nodes n ON n.label = e.parent_label AND n.key = e.parent_key
    WHERE e.child_label = %s
      AND e.child_key = %s
      AND (%s::text[] IS NULL OR e.edge_type = ANY(%s))
    UNION ALL
    SELECT n.label, n.key, n.props, n.schema_version, walk.depth + 1,
           walk.path || (n.label || ':' || n.key)
    FROM walk
    JOIN edges e ON e.child_label = walk.label AND e.child_key = walk.key
    JOIN nodes n ON n.label = e.parent_label AND n.key = e.parent_key
    WHERE walk.depth < %s
      AND (%s::text[] IS NULL OR e.edge_type = ANY(%s))
      AND NOT (n.label || ':' || n.key = ANY(walk.path))
)
SELECT label, key, props, schema_version
FROM (
    SELECT DISTINCT ON (label, key) label, key, props, schema_version, depth
    FROM walk
    ORDER BY label, key, depth
) deduped
ORDER BY depth, key
"""

TRAVERSE_DESCENDANTS_SQL = """
WITH RECURSIVE walk(label, key, props, schema_version, depth, path) AS (
    SELECT n.label, n.key, n.props, n.schema_version, 1,
           ARRAY[n.label || ':' || n.key]
    FROM edges e
    JOIN nodes n ON n.label = e.child_label AND n.key = e.child_key
    WHERE e.parent_label = %s
      AND e.parent_key = %s
      AND (%s::text[] IS NULL OR e.edge_type = ANY(%s))
    UNION ALL
    SELECT n.label, n.key, n.props, n.schema_version, walk.depth + 1,
           walk.path || (n.label || ':' || n.key)
    FROM walk
    JOIN edges e ON e.parent_label = walk.label AND e.parent_key = walk.key
    JOIN nodes n ON n.label = e.child_label AND n.key = e.child_key
    WHERE walk.depth < %s
      AND (%s::text[] IS NULL OR e.edge_type = ANY(%s))
      AND NOT (n.label || ':' || n.key = ANY(walk.path))
)
SELECT label, key, props, schema_version
FROM (
    SELECT DISTINCT ON (label, key) label, key, props, schema_version, depth
    FROM walk
    ORDER BY label, key, depth
) deduped
ORDER BY depth, key
"""


def node_from_row(row: Mapping[str, Any]) -> Node:
    """Convert a PostgreSQL row into the GraphStore value type."""
    return Node(
        label=str(row["label"]),
        key=str(row["key"]),
        props=dict(row["props"]),
        schema_version=int(row["schema_version"]),
    )


def json_props(props: Props) -> dict[str, Any]:
    """Return props in a JSONB-serializable shape."""
    return {str(key): _json_value(value) for key, value in props.items()}


def _json_value(value: Any) -> Any:  # noqa: ANN401 - graph props are JSON-like.
    if isinstance(value, Mapping):
        return {str(key): _json_value(nested) for key, nested in value.items()}
    if isinstance(value, list | tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, set | frozenset):
        return [_json_value(item) for item in sorted(value, key=repr)]
    return value
