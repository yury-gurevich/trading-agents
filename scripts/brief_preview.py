"""Print the daily brief a dispatcher fire would send for a run; send, write nothing.

Agent: tooling
Role: let the planner read a run's brief from the live graph before deploy (S234).
External I/O: environment, PostgreSQL graph (reads only), stdout/stderr.

It composes with the dispatcher's own code, so what it prints is what the operator
would get: the full brief for a run with a Snapshot, the RED brief for one without.
No Telegram port is built, and no brief marker is written.

Run it:
  PYTHONPATH=. python scripts/brief_preview.py --run-id sched-2026-09-25
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv  # noqa: E402

from orchestration.daily_brief import preview_brief  # noqa: E402
from orchestration.settings import OrchestratorSettings  # noqa: E402

if TYPE_CHECKING:
    from kernel import GraphStore


def main(argv: list[str] | None = None) -> int:
    """Print one run's brief and return a process status."""
    parser = argparse.ArgumentParser(description="print a run's daily brief")
    parser.add_argument("--run-id", required=True, help="e.g. sched-2026-09-25")
    parser.add_argument(
        "--env-file",
        default=".env",
        help="optional .env file to load before connecting to Postgres",
    )
    args = parser.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    load_dotenv(Path(args.env_file), override=False)
    if not os.environ.get("POSTGRES_DSN"):
        print("error brief preview: POSTGRES_DSN is required", file=sys.stderr)
        return 1
    graph = _live_graph()
    try:
        text = render(graph, args.run_id, now=datetime.now(tz=UTC))
    finally:
        close = getattr(graph, "close", None)
        if callable(close):
            close()
    if text is None:
        print(f"error brief preview: no RunRequest for {args.run_id}", file=sys.stderr)
        return 1
    print(text)
    return 0


def render(graph: GraphStore, run_id: str, *, now: datetime) -> str | None:
    """Return the brief a fire at ``now`` would send for ``run_id``."""
    timezone = OrchestratorSettings().operator_timezone
    return preview_brief(graph, run_id, now=now, timezone=timezone)


def _live_graph() -> GraphStore:
    from kernel.graph_env import build_graph_from_env

    return build_graph_from_env()


if __name__ == "__main__":
    raise SystemExit(main())
