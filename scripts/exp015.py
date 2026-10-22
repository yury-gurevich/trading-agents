"""Run EXP-015's stages: the panel, the walk-forward, then the holdout once (S289).

Agent: tooling
Role: the command line for the three stages, each writing outside the worktree.
External I/O: reads the S235 cache; writes the stages' files under --out.

  uv run python scripts/exp015.py panel --cache <CACHE> --out <OUT>
  uv run python scripts/exp015.py walk-forward --out <OUT>
  uv run python scripts/exp015.py holdout --out <OUT> --walk-forward-sha256 <hex>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.exp015_stages import (
    holdout_stage,
    panel_stage,
    walk_forward_stage,
)
from scripts.replay_outputs import refuse_worktree_out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run EXP-015's stages.")
    parser.add_argument("stage", choices=("panel", "walk-forward", "holdout"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--walk-forward-sha256")
    args = parser.parse_args(argv)
    out = refuse_worktree_out(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.stage == "panel":
        if args.cache is None:
            parser.error("panel needs --cache")
        record = panel_stage(args.cache, out)
        print(f"panel {record['rows']} rows, sha256 {record['panel_sha256']}")
    elif args.stage == "walk-forward":
        print(f"walk_forward.json sha256 {walk_forward_stage(out)}")
    else:
        if not args.walk_forward_sha256:
            parser.error("holdout needs --walk-forward-sha256")
        record = holdout_stage(out, args.walk_forward_sha256)
        print(f"holdout written; verdict {record['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
