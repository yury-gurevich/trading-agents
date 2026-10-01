"""Run EXP-014's arms through the S235 harness and record what each ran on (S250).

Agent: tooling
Role: run one named arm, or all, from exp014_arms.json with the history rule on.
External I/O: reads the cache; runs git read-only; writes arm folders outside the repo.

    uv run python scripts/replay_arms.py run --arm base-25 --out-root <dir>
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, Any

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts import replay_dataset  # noqa: E402
from scripts.replay_arms_record import (  # noqa: E402
    RepoState,
    cache_checksums,
    equity_dates,
    read_repo_state,
    write_benchmark,
)
from scripts.replay_outputs import refuse_worktree_out  # noqa: E402
from scripts.replay_runner import DEFAULT_PROGRESS_EVERY, run  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Callable

MANIFEST = Path(__file__).with_name("exp014_arms.json")
ALL = "all"


@dataclass(frozen=True)
class ArmSpec:
    """One arm of the manifest: its name, slippage a side and setting overrides."""

    name: str
    slippage_bps: int
    overrides: tuple[str, ...]


@dataclass(frozen=True)
class Manifest:
    """EXP-014's frozen arms (Appendix P) and the run every arm shares."""

    experiment: str
    start: date
    require_history: bool
    arms: tuple[ArmSpec, ...]


def load_manifest(path: Path = MANIFEST) -> Manifest:
    """Read `exp014_arms.json`."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return Manifest(
        experiment=str(data["experiment"]),
        start=date.fromisoformat(data["start"]),
        require_history=bool(data["require_history"]),
        arms=tuple(
            ArmSpec(arm["name"], int(arm["slippage_bps"]), tuple(arm["overrides"]))
            for arm in data["arms"]
        ),
    )


def select(manifest: Manifest, name: str) -> tuple[ArmSpec, ...]:
    """The named arm, or every arm for `all`; any other name is refused."""
    if name == ALL:
        return manifest.arms
    chosen = tuple(arm for arm in manifest.arms if arm.name == name)
    if not chosen:
        known = ", ".join(arm.name for arm in manifest.arms)
        raise ValueError(f"unknown arm {name!r}; the manifest names {known}")
    return chosen


def run_arm(
    spec: ArmSpec,
    manifest: Manifest,
    *,
    cache_dir: Path,
    out_root: Path,
    runner: Callable[..., dict[str, Any]] | None = None,
    repo: Callable[[], RepoState] | None = None,
    progress_every: int = DEFAULT_PROGRESS_EVERY,
) -> Path:
    """Replay one arm into `<out-root>/<arm>/`; `arm.json` is written last (D4)."""
    state = (repo or read_repo_state)()
    if state.dirty:
        raise ValueError("refusing to run an arm: the worktree has uncommitted changes")
    out = refuse_worktree_out(out_root / spec.name)
    (runner or run)(
        cache_dir=cache_dir,
        out=out,
        start=manifest.start,
        end=None,
        overrides=spec.overrides,
        slippage_bps=spec.slippage_bps,
        progress_every=progress_every,
        require_history=manifest.require_history,
    )
    sessions = equity_dates(out / "equity.csv")
    write_benchmark(cache_dir, sessions, out / "benchmark.csv")
    record = {
        "arm": spec.name,
        "cache": cache_checksums(cache_dir),
        "commit": state.commit,
        "dirty": state.dirty,
        "experiment": manifest.experiment,
        "first_session": sessions[0].isoformat() if sessions else None,
        "last_session": sessions[-1].isoformat() if sessions else None,
        "overrides": list(spec.overrides),
        "require_history": manifest.require_history,
        "sessions": len(sessions),
        "slippage_bps": spec.slippage_bps,
        "start": manifest.start.isoformat(),
    }
    (out / "arm.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run EXP-014's replay arms.")
    parser.add_argument("command", choices=("run",))
    parser.add_argument("--arm", required=True, help="an arm's name, or 'all'")
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=replay_dataset.CACHE)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--progress-every", type=int, default=DEFAULT_PROGRESS_EVERY)
    args = parser.parse_args(argv)
    manifest = load_manifest(args.manifest)
    for spec in select(manifest, args.arm):
        out = run_arm(
            spec,
            manifest,
            cache_dir=args.cache,
            out_root=args.out_root,
            progress_every=args.progress_every,
        )
        print(f"arm {spec.name} written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
