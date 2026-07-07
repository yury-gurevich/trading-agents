"""Pipeline observatory CLI — a human's-eye view of one persisted run.

Agent: tooling
Role: load the graph store from .env and print the observatory for a given run_id —
      per-stage I/O plus floor/ceiling/required WARNs against the locked trading
      baseline. Use after `run_local.py --real` has written the provenance chain.
External I/O: PostgreSQL (POSTGRES_DSN from .env); stdout.

Run it:
  PYTHONPATH=. python scripts/observatory.py              # run-id=local-1
  PYTHONPATH=. python scripts/observatory.py --run-id <id>
"""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    """Connect to the graph store and print the observatory for --run-id."""
    parser = argparse.ArgumentParser(description="observe a persisted graph-pull run")
    parser.add_argument("--run-id", default="local-1", help="run_id to observe")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

    from dotenv import load_dotenv

    from kernel.graph_env import build_graph_from_env
    from orchestration.packs.trading_observatory import inspect

    load_dotenv()
    graph = build_graph_from_env()
    report = inspect(graph, args.run_id)
    print(report)
    sys.exit(1 if "WARN" in report else 0)


if __name__ == "__main__":
    main()
