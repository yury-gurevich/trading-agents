"""EXP-015's stages: the panel, the walk-forward and its control, the holdout once.

Agent: tooling
Role: run each stage from the files the one before wrote, record the commit and the
      inputs' digests beside the result, refuse a holdout the walk-forward did not earn.
External I/O: reads the S235 cache; reads and writes the stages' files in an output
      directory outside the worktree.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from typing import TYPE_CHECKING

from scripts.exp015_evaluate import score_fold
from scripts.exp015_folds import holdout, walk_forward
from scripts.exp015_models import Trainer, lightgbm_trainer
from scripts.exp015_panel import build_panel
from scripts.exp015_ranks import ranked_features
from scripts.exp015_report import holdout_page, walk_forward_page
from scripts.exp015_rule import holdout_reading, verdict, walk_forward_reading
from scripts.exp015_spec import EXPERIMENT, FOLD_YEARS, HOLDOUT_START, SEED
from scripts.exp015_store import (
    Panel,
    load_panel,
    panel_digest,
    save_panel,
    shuffled,
)
from scripts.replay_arms_record import cache_checksums, read_repo_state
from scripts.replay_cache import load_replay_cache
from scripts.replay_series import bars_by_line
from scripts.replay_settings import build_effective_settings
from scripts.sp500_guards import load_known_moves

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

WALK_FORWARD = "walk_forward.json"
HOLDOUT = "holdout.json"


def panel_stage(cache: Path, out: Path) -> dict[str, object]:
    """Build and save the panel over every cached session, and what built it."""
    commit = _clean_commit()
    context = load_replay_cache(cache)
    errors: dict[str, tuple[date, ...]] = {}
    for move in load_known_moves():
        if move.kind == "adjustment-error":
            errors[move.line] = (*errors.get(move.line, ()), move.date)
    panel, counts = build_panel(
        context,
        build_effective_settings(()),
        bars_by_line(context.universe.bars),
        errors,
        context.universe.sessions,
    )
    save_panel(out, panel)
    record = {
        "experiment": EXPERIMENT,
        "commit": commit,
        "cache": cache_checksums(cache),
        "panel_sha256": panel_digest(panel),
        "rows": len(panel.lines),
        "primary_rows": int(panel.primary.sum()),
        "secondary_rows": int(panel.secondary.sum()),
        "first_session": str(panel.sessions[0]) if len(panel.lines) else None,
        "last_session": str(panel.sessions[-1]) if len(panel.lines) else None,
        "counts": counts,
    }
    _write(out / "panel.json", record)
    return record


def walk_forward_stage(
    out: Path,
    trainer: Trainer = lightgbm_trainer,
    years: Sequence[int] = FOLD_YEARS,
    resamples: int | None = None,
) -> str:
    """Score the folds (primary, shuffled control, secondary); the file's SHA-256."""
    commit, panel = _clean_commit(), load_panel(out)
    calendar = _calendar(panel)
    folds = walk_forward(calendar, years)
    primary = _scored(panel.take(panel.primary), folds, trainer)
    control = _scored(shuffled(panel.take(panel.primary), SEED), folds, trainer)
    secondary = _scored(panel.take(panel.secondary), folds, trainer)
    reading = walk_forward_reading(primary, control, **_boot(resamples))
    record = {
        "experiment": EXPERIMENT,
        "commit": commit,
        "panel_sha256": panel_digest(panel),
        "folds": primary,
        "control": control,
        "secondary": secondary,
        "reading": reading,
        "verdict": verdict(reading, None),
    }
    path = _write(out / WALK_FORWARD, record)
    (out / "walk_forward.md").write_text(walk_forward_page(record), encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def holdout_stage(
    out: Path,
    walk_forward_sha256: str,
    trainer: Trainer = lightgbm_trainer,
    start: date = HOLDOUT_START,
) -> dict[str, object]:
    """Touch the holdout once: after a recorded walk-forward whose control passed."""
    if (out / HOLDOUT).exists():
        raise ValueError("the holdout was touched already: holdout.json exists")
    path = out / WALK_FORWARD
    if (
        not path.exists()
        or hashlib.sha256(path.read_bytes()).hexdigest() != walk_forward_sha256
    ):
        raise ValueError("walk_forward.json is missing or is not the recorded one")
    walk = json.loads(path.read_text(encoding="utf-8"))
    if walk["verdict"] == "STOPPED":
        raise ValueError("the shuffled-target control failed: the experiment stopped")
    commit, panel = _clean_commit(), load_panel(out)
    fold = holdout(_calendar(panel), start)
    primary = _scored(panel.take(panel.primary), (fold,), trainer)[0]
    secondary = _scored(panel.take(panel.secondary), (fold,), trainer)[0]
    reading = holdout_reading(primary)
    record = {
        "experiment": EXPERIMENT,
        "commit": commit,
        "walk_forward_sha256": walk_forward_sha256,
        "holdout": primary,
        "secondary": secondary,
        "reading": reading,
        "verdict": verdict(walk["reading"], reading),
    }
    _write(out / HOLDOUT, record)
    (out / "verdict.md").write_text(holdout_page(walk, record), encoding="utf-8")
    return record


def _scored(panel: Panel, folds: Sequence, trainer: Trainer) -> list[dict[str, object]]:
    x = ranked_features(panel)
    return [score_fold(panel, x, fold, trainer) for fold in folds]


def _calendar(panel: Panel) -> tuple[date, ...]:
    return tuple(
        date.fromisoformat(day) for day in sorted(set(panel.sessions.tolist()))
    )


def _boot(resamples: int | None) -> dict[str, int]:
    return {} if resamples is None else {"resamples": resamples}


def _clean_commit() -> str:
    state = read_repo_state()
    if state.dirty:
        raise ValueError(
            "refusing to run EXP-015: the worktree has uncommitted changes"
        )
    return state.commit


def _write(path: Path, record: dict[str, object]) -> Path:
    path.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path
