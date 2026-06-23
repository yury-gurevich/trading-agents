"""Compare two Neo4j Aura databases for structural identity.

Agent: tooling
Role: connect to the Professional and Free Aura instances, compare per-label
      node counts and per-type relationship counts, and print a side-by-side
      diff table with an IDENTICAL / DIVERGED verdict.
      Reads credentials from infra/aura-instance.local.json (Professional)
      and infra/aura-free.local.json (Free); both files must exist.
      Exit 0 = identical, 1 = diverged, 2 = connection / credential error.

Run it:
  PYTHONPATH=. python scripts/compare_aura.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from neo4j import Driver


def _load_creds(path: Path) -> dict[str, object]:
    if not path.exists():
        print(f"ERROR: {path} not found.", file=sys.stderr)
        sys.exit(2)
    raw: dict[str, object] = json.loads(path.read_text(encoding="utf-8"))
    return raw


def _query(driver: Driver, cypher: str) -> list[dict[str, object]]:
    with driver.session(database="neo4j") as session:
        return [dict(r) for r in session.run(cypher)]


def _node_counts(driver: Driver) -> dict[str, int]:
    rows = _query(
        driver,
        "MATCH (n) RETURN labels(n)[0] AS label, count(*) AS cnt ORDER BY label",
    )
    return {
        str(r["label"]): cast("int", r["cnt"]) for r in rows if r["label"] is not None
    }


def _rel_counts(driver: Driver) -> dict[str, int]:
    cypher = (
        "MATCH ()-[r]->() RETURN type(r) AS rel_type, count(*) AS cnt ORDER BY rel_type"
    )
    rows = _query(driver, cypher)
    return {str(r["rel_type"]): cast("int", r["cnt"]) for r in rows}


def _total(driver: Driver) -> tuple[int, int]:
    nodes = cast("int", _query(driver, "MATCH (n) RETURN count(n) AS c")[0]["c"])
    rels = cast("int", _query(driver, "MATCH ()-[r]->() RETURN count(r) AS c")[0]["c"])
    return nodes, rels


def _print_table(
    title: str,
    prof: dict[str, int],
    free: dict[str, int],
) -> bool:
    """Print side-by-side counts. Returns True if all rows match."""
    all_keys = sorted(set(prof) | set(free))
    identical = True
    w = max((len(k) for k in all_keys), default=8)
    print(f"\n{title}")
    print(f"  {'Name':<{w}}  {'Professional':>14}  {'Free':>14}  {'Match':>6}")
    print(f"  {'-' * w}  {'-' * 14}  {'-' * 14}  {'-' * 6}")
    for k in all_keys:
        p = prof.get(k, 0)
        f = free.get(k, 0)
        match = "✓" if p == f else "✗"
        if p != f:
            identical = False
        print(f"  {k:<{w}}  {p:>14,}  {f:>14,}  {match:>6}")
    return identical


def main() -> None:
    """Compare the two Aura databases and exit 0 if identical."""
    repo = Path(__file__).parent.parent
    prof_path = repo / "infra" / "aura-instance.local.json"
    free_path = repo / "infra" / "aura-free.local.json"

    prof_creds = _load_creds(prof_path)
    free_creds = _load_creds(free_path)

    # Validate passwords present
    for _label, creds, path in (
        ("Professional", prof_creds, prof_path),
        ("Free", free_creds, free_path),
    ):
        if not creds.get("password"):
            print(
                f"ERROR: {path} has no 'password' field. "
                f"Add it manually (shown once at instance creation).",
                file=sys.stderr,
            )
            sys.exit(2)

    try:
        from neo4j import GraphDatabase
    except ImportError:
        print("ERROR: neo4j driver not installed.", file=sys.stderr)
        print("Run: uv sync --group dev", file=sys.stderr)
        sys.exit(2)

    print("Connecting to Professional instance ...")
    try:
        prof_driver = GraphDatabase.driver(
            prof_creds["connection_url"],
            auth=(prof_creds.get("username", "neo4j"), prof_creds["password"]),
        )
        prof_driver.verify_connectivity()
    except Exception as exc:
        print(f"ERROR: Professional connection failed: {exc}", file=sys.stderr)
        sys.exit(2)

    print("Connecting to Free instance ...")
    try:
        free_driver = GraphDatabase.driver(
            free_creds["connection_url"],
            auth=(free_creds.get("username", "neo4j"), free_creds["password"]),
        )
        free_driver.verify_connectivity()
    except Exception as exc:
        print(f"ERROR: Free connection failed: {exc}", file=sys.stderr)
        sys.exit(2)

    print("\nQuerying both instances ...")
    try:
        prof_nodes = _node_counts(prof_driver)
        free_nodes = _node_counts(free_driver)
        prof_rels = _rel_counts(prof_driver)
        free_rels = _rel_counts(free_driver)
        prof_total_n, prof_total_r = _total(prof_driver)
        free_total_n, free_total_r = _total(free_driver)
    finally:
        prof_driver.close()
        free_driver.close()

    # ── summary line ──────────────────────────────────────────────────────────
    print(f"\n{'':=<60}")
    print(f"  Professional:  {prof_total_n:,} nodes  {prof_total_r:,} rels")
    print(f"  Free:          {free_total_n:,} nodes  {free_total_r:,} rels")
    print(f"{'':=<60}")

    nodes_ok = _print_table("NODE COUNTS (by label)", prof_nodes, free_nodes)
    rels_ok = _print_table("RELATIONSHIP COUNTS (by type)", prof_rels, free_rels)

    print(f"\n{'':=<60}")
    if nodes_ok and rels_ok:
        print("  VERDICT:  OK  IDENTICAL")
        print("  Safe to switch to Free and pause Professional.")
        print(f"{'':=<60}")
        sys.exit(0)
    else:
        print("  VERDICT:  !!  DIVERGED — databases differ (see above).")
        if free_total_n == 0:
            print("  Free instance is empty — cross-tier overwrite rejected.")
            print("  Run a fresh batch on Free; old provenance data not needed.")
        print(f"{'':=<60}")
        sys.exit(1)


if __name__ == "__main__":
    main()
