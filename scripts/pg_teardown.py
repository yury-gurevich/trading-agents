"""Delete stamped PostgreSQL graph test rows by key prefix.

Agent: tooling
Role: clean live Postgres functionality-check rows without adding destructive ops to
      the GraphStore port.
External I/O: PostgreSQL database.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

import psycopg
from dotenv import load_dotenv

_RUN_ARTIFACT_LABELS = (
    "RunRequest",
    "MarketData",
    "RegimeContext",
    "ScanRun",
    "Candidate",
    "AnalystRun",
    "Recommendation",
    "PMRun",
    "OrderIntent",
    "ExecutionRun",
    "Fill",
    "Position",
    "MonitorRun",
    "CloseDecision",
    "Snapshot",
    "TradeNarrative",
)


def main(argv: list[str] | None = None) -> int:
    """Run the FK-ordered teardown and print deleted row counts."""
    parser = argparse.ArgumentParser()
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--prefix", help="required key prefix stamp")
    target.add_argument(
        "--run-id",
        help="delete the stamped RunRequest lineage, including random child keys",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="explicit .env path containing POSTGRES_DSN",
    )
    parser.add_argument(
        "--contains",
        action="store_true",
        help="match the stamp anywhere in the graph key instead of only as a prefix",
    )
    args = parser.parse_args(argv)
    if args.prefix is not None and not args.prefix:
        parser.error("--prefix must be non-empty")
    if args.run_id is not None and not args.run_id:
        parser.error("--run-id must be non-empty")

    load_dotenv(Path(args.env_file), override=False)
    dsn = os.environ.get("POSTGRES_DSN", "")
    if not dsn:
        parser.error("POSTGRES_DSN is required")

    with (
        psycopg.connect(dsn, connect_timeout=10) as connection,
        connection.cursor() as cursor,
    ):
        if args.run_id is not None:
            edges, nodes = _delete_run_artifacts(cursor, args.run_id)
        else:
            edges, nodes = _delete_by_key_pattern(
                cursor,
                _like_pattern(str(args.prefix), contains=args.contains),
            )
    print(f"deleted_edges={edges} deleted_nodes={nodes}")
    return 0


def _delete_by_key_pattern(cursor: Any, pattern: str) -> tuple[int, int]:  # noqa: ANN401
    cursor.execute(
        "DELETE FROM edges "
        "WHERE parent_key LIKE %s ESCAPE '\\' "
        "OR child_key LIKE %s ESCAPE '\\'",
        (pattern, pattern),
    )
    edges = int(cursor.rowcount)
    cursor.execute(
        "DELETE FROM nodes WHERE key LIKE %s ESCAPE '\\'",
        (pattern,),
    )
    return edges, int(cursor.rowcount)


def _delete_run_artifacts(cursor: Any, run_id: str) -> tuple[int, int]:  # noqa: ANN401
    pattern = _like_pattern(run_id, contains=True)
    cursor.execute(
        """
        WITH RECURSIVE target(label, key) AS (
            SELECT label, key
            FROM nodes
            WHERE key LIKE %s ESCAPE '\\'
            UNION
            SELECT neighbor.label, neighbor.key
            FROM target t
            JOIN LATERAL (
                SELECT e.child_label AS label, e.child_key AS key
                FROM edges e
                WHERE e.parent_label = t.label AND e.parent_key = t.key
                UNION
                SELECT e.parent_label AS label, e.parent_key AS key
                FROM edges e
                WHERE e.child_label = t.label AND e.child_key = t.key
            ) neighbor ON true
            JOIN nodes n ON n.label = neighbor.label AND n.key = neighbor.key
            WHERE n.label = ANY(%s)
        )
        SELECT label, key
        FROM target
        """,
        (pattern, list(_RUN_ARTIFACT_LABELS)),
    )
    rows = [(str(label), str(key)) for label, key in cursor.fetchall()]
    if not rows:
        return (0, 0)

    cursor.execute(
        "CREATE TEMP TABLE pg_teardown_target "
        "(label text NOT NULL, key text NOT NULL) ON COMMIT DROP"
    )
    cursor.executemany(
        "INSERT INTO pg_teardown_target (label, key) VALUES (%s, %s)",
        rows,
    )
    cursor.execute(
        "DELETE FROM edges e "
        "WHERE EXISTS ("
        "  SELECT 1 FROM pg_teardown_target t "
        "  WHERE t.label = e.parent_label AND t.key = e.parent_key"
        ") OR EXISTS ("
        "  SELECT 1 FROM pg_teardown_target t "
        "  WHERE t.label = e.child_label AND t.key = e.child_key"
        ")"
    )
    edges = int(cursor.rowcount)
    cursor.execute(
        "DELETE FROM nodes n "
        "WHERE EXISTS ("
        "  SELECT 1 FROM pg_teardown_target t "
        "  WHERE t.label = n.label AND t.key = n.key"
        ")"
    )
    return edges, int(cursor.rowcount)


def _like_pattern(prefix: str, *, contains: bool) -> str:
    escaped = prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%" if contains else f"{escaped}%"


if __name__ == "__main__":
    raise SystemExit(main())
