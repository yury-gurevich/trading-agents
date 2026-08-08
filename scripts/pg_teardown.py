"""Delete stamped PostgreSQL graph test rows by key prefix.

Agent: tooling
Role: clean live Postgres functionality-check rows without adding destructive ops to
      the GraphStore port.
External I/O: PostgreSQL database.

`--run-id` verifies itself: it re-reads the run's stamps after deleting and exits
non-zero if any deletable row survived. Printing a count and exiting 0 while orphans
remained is the defect DL-94 records — a teardown that silently under-deletes quietly
corrupts the functionality-check register's central claim.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

import psycopg
from dotenv import load_dotenv
from scripts.pg_teardown_targets import (
    PROTECTED_LABELS,
    collect,
    like_pattern,
    protected_matches,
    protected_neighbours,
    survivors,
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
            return _run_id_teardown(cursor, str(args.run_id))
        pattern = like_pattern(str(args.prefix), contains=args.contains)
        broker_rows = protected_matches(cursor, [pattern])
        edges, nodes = _delete_by_key_pattern(cursor, pattern)
    print(f"deleted_edges={edges} deleted_nodes={nodes}")
    if broker_rows:
        print(
            f"warning: {broker_rows} deleted row(s) carry a broker-state label "
            f"({', '.join(PROTECTED_LABELS)}) — see DL-44 before trusting the book"
        )
    return 0


def _run_id_teardown(cursor: Any, run_id: str) -> int:  # noqa: ANN401
    """Delete a run's artifacts, then prove none of its stamps survived."""
    targets = collect(cursor, run_id)
    kept = protected_neighbours(cursor, targets)
    edges, nodes = _delete_targets(cursor, targets)
    print(f"deleted_edges={edges} deleted_nodes={nodes} protected_kept={kept}")

    remaining = survivors(cursor, run_id, targets)
    if remaining:
        print(f"ORPHANS REMAIN for {run_id}: {len(remaining)} row(s) still stamped")
        for label, key in remaining:
            print(f"  {label} {key}")
        return 1
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


def _delete_targets(
    cursor: Any,  # noqa: ANN401
    targets: list[tuple[str, str]],
) -> tuple[int, int]:
    """Delete exactly the enumerated rows, edges first."""
    if not targets:
        return (0, 0)
    cursor.execute(
        "CREATE TEMP TABLE pg_teardown_target "
        "(label text NOT NULL, key text NOT NULL) ON COMMIT DROP"
    )
    cursor.executemany(
        "INSERT INTO pg_teardown_target (label, key) VALUES (%s, %s)",
        targets,
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


if __name__ == "__main__":
    raise SystemExit(main())
