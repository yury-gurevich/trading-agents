"""CLI for S237 read-only live fidelity export.

Agent: tooling
Role: parse export arguments and delegate to the graph projection.
External I/O: reads configured graph store and writes JSON outside the worktree.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.fidelity_exporter import export_sessions  # noqa: E402

from kernel.graph_env import build_graph_from_env  # noqa: E402


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Export S237 live run fidelity JSON.")
    parser.add_argument("command", choices=("export",))
    parser.add_argument("--start", required=True, type=date.fromisoformat)
    parser.add_argument("--end", required=True, type=date.fromisoformat)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    export_sessions(
        build_graph_from_env(),
        start=args.start,
        end=args.end,
        out=args.out,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
