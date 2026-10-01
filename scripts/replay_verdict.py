"""Score EXP-014's arms into a verdict with a 95 % interval, by Appendix P (S250).

Agent: tooling
Role: load the arms, refuse what does not belong together, score, and write the verdict.
External I/O: reads arm folders; writes verdict.json and verdict.md outside the repo.

    uv run python scripts/replay_verdict.py score --out-root <dir>

Exit 0 with a verdict, 2 with a refusal (both write the two files).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.replay_arms import MANIFEST, load_manifest  # noqa: E402
from scripts.replay_outputs import refuse_worktree_out  # noqa: E402
from scripts.replay_verdict_load import load_arms  # noqa: E402
from scripts.replay_verdict_report import verdict_document, write_verdict  # noqa: E402
from scripts.replay_verdict_score import RESAMPLES, score_arms  # noqa: E402

REFUSED = 2


def score_out_root(
    out_root: Path, manifest_path: Path = MANIFEST, *, resamples: int = RESAMPLES
) -> dict[str, Any]:
    """Load, check, score and write; return the document written."""
    out_root = refuse_worktree_out(out_root)
    manifest = load_manifest(manifest_path)
    loaded = load_arms(out_root, manifest)
    scored = None if loaded.refusals else score_arms(loaded.arms, resamples=resamples)
    document = verdict_document(manifest, loaded, scored)
    write_verdict(out_root, document)
    return document


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Score EXP-014's arms.")
    parser.add_argument("command", choices=("score",))
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument(
        "--resamples",
        type=int,
        default=RESAMPLES,
        help="Appendix P's 10,000; anything else is marked as not Appendix P",
    )
    args = parser.parse_args(argv)
    document = score_out_root(args.out_root, args.manifest, resamples=args.resamples)
    page = (args.out_root / "verdict.md").read_text(encoding="utf-8")
    print("\n".join(page.splitlines()[:3]))
    for item in document["refusals"]:
        print(f"refused: {item['arm']}: {item['reason']}")
    return 0 if document["verdict"] else REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
