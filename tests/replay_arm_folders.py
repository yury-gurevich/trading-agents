"""Write synthetic EXP-014 arm folders as `replay_arms.py` would (S250 tests).

Agent: tooling
Role: lay out arm.json, equity.csv, benchmark.csv and summary.json from invented arms.
External I/O: local tmp files only.
"""

from __future__ import annotations

import csv
import json
from typing import TYPE_CHECKING, Any

from scripts.replay_arms import load_manifest
from tests.replay_verdict_fixtures import five_arms

if TYPE_CHECKING:
    from pathlib import Path

    from scripts.replay_verdict_score import ArmSeries

COMMIT = "c" * 40  # a placeholder commit; low entropy on purpose
CACHE = {"sp500_bars.csv.gz": "b" * 12, "sp500_sectors.csv.gz": "absent"}


def write_arms(out_root: Path, base_drift: float = 0.0, count: int = 121) -> Path:
    """Write all five manifest arms under `out_root` from synthetic series."""
    manifest = load_manifest()
    arms = five_arms(base_drift, 0.0, count=count)
    for spec in manifest.arms:
        write_arm(out_root, arms[spec.name], spec.slippage_bps, list(spec.overrides))
    return out_root


def write_arm(
    out_root: Path, arm: ArmSeries, slippage_bps: int, overrides: list[str]
) -> None:
    """One arm folder, recorded as a clean run of the committed manifest."""
    folder = out_root / arm.name
    folder.mkdir(parents=True)
    _csv(
        folder / "equity.csv",
        ["date", "equity_cents", "long_cents"],
        [[day.isoformat(), equity, held] for day, equity, held in arm.points],
    )
    _csv(
        folder / "benchmark.csv",
        ["date", "close"],
        [[day.isoformat(), repr(close)] for day, close in sorted(arm.closes.items())],
    )
    summary = {"absent_inputs": {"member_sessions_below_required_history": 7}}
    (folder / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    record = {
        "arm": arm.name,
        "cache": dict(CACHE),
        "commit": COMMIT,
        "dirty": False,
        "experiment": "EXP-014",
        "first_session": arm.points[0][0].isoformat(),
        "last_session": arm.points[-1][0].isoformat(),
        "overrides": overrides,
        "require_history": True,
        "sessions": len(arm.points),
        "slippage_bps": slippage_bps,
        "start": "2017-01-03",
    }
    edit_record(folder, record)


def edit_record(folder: Path, record: dict[str, Any]) -> None:
    """Write `record` as the folder's arm.json."""
    (folder / "arm.json").write_text(json.dumps(record, indent=2), encoding="utf-8")


def read_record(folder: Path) -> dict[str, Any]:
    """The folder's arm.json."""
    return json.loads((folder / "arm.json").read_text(encoding="utf-8"))


def _csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
