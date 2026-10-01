"""CLI for the S235 synthetic replay pipeline.

Agent: tooling
Role: parse replay arguments and delegate to the script-local runner.
External I/O: local cache input and out-of-worktree replay output files.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts import replay_dataset  # noqa: E402
from scripts.replay_runner import (  # noqa: E402
    DEFAULT_PROGRESS_EVERY,
    DEFAULT_SLIPPAGE_BPS,
    run,
)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run S235 cached pipeline replay.")
    parser.add_argument("command", choices=("run",))
    parser.add_argument("--cache", type=Path, default=replay_dataset.CACHE)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--start", type=date.fromisoformat)
    parser.add_argument("--end", type=date.fromisoformat)
    parser.add_argument("--set", action="append", default=[])
    parser.add_argument("--slippage-bps", type=int, default=DEFAULT_SLIPPAGE_BPS)
    parser.add_argument("--universe-file", type=Path)
    parser.add_argument("--progress-every", type=int, default=DEFAULT_PROGRESS_EVERY)
    parser.add_argument(
        "--require-history",
        action="store_true",
        help="withhold an unheld line until its window holds the analyst's bars",
    )
    args = parser.parse_args(argv)
    run(
        cache_dir=args.cache,
        out=args.out,
        start=args.start,
        end=args.end,
        overrides=tuple(args.set),
        slippage_bps=args.slippage_bps,
        universe_file=args.universe_file,
        progress_every=args.progress_every,
        require_history=args.require_history,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
