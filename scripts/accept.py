"""Layer-3 acceptance gate CLI — PASS/FAIL a persisted run.

Agent: tooling
Role: load Neo4j from .env and run the acceptance gate for a given run_id — every
      per-stage invariant + the cross-stage conservation boundaries. Exits non-zero
      on FAIL, so it can gate a deploy. Use after a `run_local.py --real` run.
External I/O: Neo4j (NEO4J_URI from .env); stdout; exit code.

Run it:
  PYTHONPATH=. python scripts/accept.py --run-id <id>
"""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    """Connect to Neo4j and accept/reject the run for --run-id."""
    parser = argparse.ArgumentParser(description="Layer-3 acceptance gate")
    parser.add_argument("--run-id", default="local-1", help="run_id to accept")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

    from dotenv import load_dotenv

    from kernel.graph_env import build_graph_from_env
    from orchestration.packs.trading_acceptance import accept_run, render_acceptance

    load_dotenv()
    graph = build_graph_from_env()
    result = accept_run(graph, args.run_id)
    print(render_acceptance(result))
    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
