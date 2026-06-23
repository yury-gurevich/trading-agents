"""Compare two Neo4j databases for structural identity.

Agent: tooling
Role: connect to two Neo4j instances, compare per-label node counts and
      per-type relationship counts, and print a side-by-side diff table
      with an IDENTICAL / DIVERGED verdict.
      Each instance is described by a JSON credentials file containing at
      minimum: connection_url, password (and optionally username).
      General-purpose: works for any two Neo4j instances — Aura→Aura,
      Aura→local, region migration, tier migration, disaster-recovery checks.
      Exit 0 = identical, 1 = diverged, 2 = connection / credential error.

Defaults (Aura Professional → Free):
  --src  infra/aura-instance.local.json
  --dst  infra/aura-free.local.json

Run it:
  PYTHONPATH=. python scripts/compare_aura.py
  PYTHONPATH=. python scripts/compare_aura.py \\
      --src infra/aura-instance.local.json \\
      --dst infra/aura-sydney.local.json \\
      --src-label "Sydney" --dst-label "US-Central"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from neo4j import Driver

_REPO = Path(__file__).parent.parent
_DEFAULT_SRC = _REPO / "infra" / "aura-instance.local.json"
_DEFAULT_DST = _REPO / "infra" / "aura-free.local.json"


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
    src: dict[str, int],
    dst: dict[str, int],
    src_label: str = "Source",
    dst_label: str = "Destination",
) -> bool:
    """Print side-by-side counts. Returns True if all rows match."""
    all_keys = sorted(set(src) | set(dst))
    identical = True
    w = max((len(k) for k in all_keys), default=8)
    col = 14
    print(f"\n{title}")
    sl, dl = src_label[:col], dst_label[:col]
    print(f"  {'Name':<{w}}  {sl:>{col}}  {dl:>{col}}  {'Match':>6}")
    print(f"  {'-' * w}  {'-' * col}  {'-' * col}  {'-' * 6}")
    for k in all_keys:
        p = src.get(k, 0)
        d = dst.get(k, 0)
        match = "OK" if p == d else "!!"
        if p != d:
            identical = False
        print(f"  {k:<{w}}  {p:>{col},}  {d:>{col},}  {match:>6}")
    return identical


def main() -> None:
    """Compare two Neo4j databases and exit 0 if identical."""
    parser = argparse.ArgumentParser(description="compare two Neo4j instances")
    parser.add_argument(
        "--src",
        type=Path,
        default=_DEFAULT_SRC,
        help="source credentials JSON (default: infra/aura-instance.local.json)",
    )
    parser.add_argument(
        "--dst",
        type=Path,
        default=_DEFAULT_DST,
        help="destination credentials JSON (default: infra/aura-free.local.json)",
    )
    parser.add_argument(
        "--src-label",
        default="Source",
        help="display name for source instance (default: Source)",
    )
    parser.add_argument(
        "--dst-label",
        default="Destination",
        help="display name for destination instance (default: Destination)",
    )
    args = parser.parse_args()

    prof_path: Path = args.src
    free_path: Path = args.dst
    src_label: str = args.src_label
    dst_label: str = args.dst_label

    prof_creds = _load_creds(prof_path)
    free_creds = _load_creds(free_path)

    # Validate passwords present
    for _label, creds, path in (
        (src_label, prof_creds, prof_path),
        (dst_label, free_creds, free_path),
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

    print(f"Connecting to {src_label} instance ...")
    try:
        prof_driver = GraphDatabase.driver(
            prof_creds["connection_url"],
            auth=(prof_creds.get("username", "neo4j"), prof_creds["password"]),
        )
        prof_driver.verify_connectivity()
    except Exception as exc:
        print(f"ERROR: {src_label} connection failed: {exc}", file=sys.stderr)
        sys.exit(2)

    print(f"Connecting to {dst_label} instance ...")
    try:
        free_driver = GraphDatabase.driver(
            free_creds["connection_url"],
            auth=(free_creds.get("username", "neo4j"), free_creds["password"]),
        )
        free_driver.verify_connectivity()
    except Exception as exc:
        print(f"ERROR: {dst_label} connection failed: {exc}", file=sys.stderr)
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
    print(f"  {src_label + ':':20s}  {prof_total_n:,} nodes  {prof_total_r:,} rels")
    print(f"  {dst_label + ':':20s}  {free_total_n:,} nodes  {free_total_r:,} rels")
    print(f"{'':=<60}")

    nodes_ok = _print_table(
        f"NODE COUNTS (by label) — {src_label} vs {dst_label}",
        prof_nodes,
        free_nodes,
        src_label=src_label,
        dst_label=dst_label,
    )
    rels_ok = _print_table(
        f"RELATIONSHIP COUNTS (by type) — {src_label} vs {dst_label}",
        prof_rels,
        free_rels,
        src_label=src_label,
        dst_label=dst_label,
    )

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
