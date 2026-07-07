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

import psycopg
from dotenv import load_dotenv


def main(argv: list[str] | None = None) -> int:
    """Run the FK-ordered teardown and print deleted row counts."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", required=True, help="required key prefix stamp")
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
    if not args.prefix:
        parser.error("--prefix must be non-empty")

    load_dotenv(Path(args.env_file), override=False)
    dsn = os.environ.get("POSTGRES_DSN", "")
    if not dsn:
        parser.error("POSTGRES_DSN is required")

    pattern = _like_pattern(args.prefix, contains=args.contains)
    with (
        psycopg.connect(dsn, connect_timeout=10) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            "DELETE FROM edges "
            "WHERE parent_key LIKE %s ESCAPE '\\' "
            "OR child_key LIKE %s ESCAPE '\\'",
            (pattern, pattern),
        )
        edges = cursor.rowcount
        cursor.execute(
            "DELETE FROM nodes WHERE key LIKE %s ESCAPE '\\'",
            (pattern,),
        )
        nodes = cursor.rowcount
    print(f"deleted_edges={edges} deleted_nodes={nodes}")
    return 0


def _like_pattern(prefix: str, *, contains: bool) -> str:
    escaped = prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%" if contains else f"{escaped}%"


if __name__ == "__main__":
    raise SystemExit(main())
