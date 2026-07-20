"""Scheduled dispatcher entrypoint for Container Apps Jobs.

Agent: tooling
Role: load environment, require PostgreSQL, and place or skip today's RunRequest.
External I/O: environment, PostgreSQL graph, stdout/stderr.

Run it:
  PYTHONPATH=. python scripts/dispatch_scheduled_run.py
  PYTHONPATH=. python scripts/dispatch_scheduled_run.py --as-of 2026-07-04
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import UTC, date, datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv  # noqa: E402

from orchestration.scheduled_dispatch import (  # noqa: E402
    CalendarWindowExceededError,
    decide_scheduled_run,
    place_scheduled_run,
)


def main(argv: list[str] | None = None) -> int:
    """Run one scheduled dispatch attempt and return a process status."""
    parser = argparse.ArgumentParser(description="scheduled graph-pull dispatcher")
    parser.add_argument(
        "--as-of",
        default=os.environ.get("DISPATCHER_AS_OF", ""),
        help="YYYY-MM-DD trading date override; defaults to today's UTC date",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="optional .env file to load before connecting to Postgres",
    )
    args = parser.parse_args(argv)

    _configure_stdout()
    load_dotenv(Path(args.env_file), override=False)
    as_of = _as_of_date(args.as_of)
    try:
        decision = decide_scheduled_run(as_of)
    except CalendarWindowExceededError as exc:
        print(f"error calendar-window-exceeded: {exc}", file=sys.stderr)
        return 1
    if decision.action == "skip":
        print(f"skipped {decision.run_id} reason={decision.reason}")
        return 0

    if not os.environ.get("POSTGRES_DSN"):
        print(
            "error scheduled dispatcher failed: POSTGRES_DSN is required",
            file=sys.stderr,
        )
        return 1

    try:
        graph = _live_graph()
        try:
            result = place_scheduled_run(graph, as_of=as_of)
        finally:
            close = getattr(graph, "close", None)
            if callable(close):
                close()
    except CalendarWindowExceededError as exc:
        print(f"error calendar-window-exceeded: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(
            f"error scheduled dispatcher failed: {type(exc).__name__}",
            file=sys.stderr,
        )
        return 1

    print(f"{result.action} {result.run_id} reason={result.reason}")
    return 0


def _as_of_date(raw: str) -> date:
    if raw:
        return date.fromisoformat(raw)
    return datetime.now(tz=UTC).date()


def _configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]


def _live_graph() -> object:
    from kernel.graph_env import build_graph_from_env

    return build_graph_from_env()


if __name__ == "__main__":
    raise SystemExit(main())
