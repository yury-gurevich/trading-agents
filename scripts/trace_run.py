"""Post-run batch trace CLI — print per-stage metrics from a persisted pipeline run.

Agent: tooling
Role: load Neo4j from .env and print the batch trace for a given run_id. Intended
      for use after `run_local.py --real` has written the provenance chain to Neo4j.
External I/O: Neo4j (NEO4J_URI from .env).

Run it:
  PYTHONPATH=. python scripts/trace_run.py              # traces run-id=local-1
  PYTHONPATH=. python scripts/trace_run.py --run-id <id>
"""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    """Connect to Neo4j and print the batch trace for --run-id."""
    parser = argparse.ArgumentParser(description="trace a persisted graph-pull run")
    parser.add_argument("--run-id", default="local-1", help="run_id to trace")
    args = parser.parse_args()

    from dotenv import load_dotenv

    from kernel.graph_env import build_graph_from_env
    from orchestration.batch_trace import print_trace

    load_dotenv()
    graph = build_graph_from_env()
    complete = print_trace(graph, args.run_id)
    sys.exit(0 if complete == 7 else 1)


if __name__ == "__main__":
    main()
