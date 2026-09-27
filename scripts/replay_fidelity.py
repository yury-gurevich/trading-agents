"""CLI for S237 replay fidelity reports.

Agent: tooling
Role: parse fidelity replay arguments and write layer outputs.
External I/O: reads exported JSON/cache directories and writes reports outside repo.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.replay_fidelity_compare import run_fidelity  # noqa: E402


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run S237 fidelity comparison.")
    parser.add_argument("command", choices=("run",))
    parser.add_argument("--export", required=True, type=Path)
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    run_fidelity(export=args.export, cache=args.cache, out=args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
