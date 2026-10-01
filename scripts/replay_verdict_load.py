"""Read EXP-014's arm folders and refuse arms that do not belong together (S250).

Agent: tooling
Role: load each arm's points and SPY closes; check it against the manifest and the rest.
External I/O: reads arm folders under the out-root.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING, Any

from scripts.replay_verdict_rule import BASE_ARM
from scripts.replay_verdict_score import ArmSeries

if TYPE_CHECKING:
    from pathlib import Path

    from scripts.replay_arms import ArmSpec, Manifest
    from scripts.replay_verdict_stats import Point

ARM_FILES = ("arm.json", "equity.csv", "benchmark.csv", "summary.json")
_SHARED = (("commit", "commit differs"), ("cache", "cache checksums differ"))


@dataclass
class LoadedArms:
    """The arms that loaded, what each recorded, and every refusal found."""

    arms: dict[str, ArmSeries] = field(default_factory=dict)
    records: dict[str, dict[str, Any]] = field(default_factory=dict)
    absent_inputs: dict[str, dict[str, Any]] = field(default_factory=dict)
    refusals: list[dict[str, str]] = field(default_factory=list)


def load_arms(out_root: Path, manifest: Manifest) -> LoadedArms:
    """Every manifest arm from `<out-root>/<arm>/`, refused by name if it misfits."""
    loaded = LoadedArms()
    for spec in manifest.arms:
        folder = out_root / spec.name
        missing = [name for name in ARM_FILES if not (folder / name).is_file()]
        if missing:
            loaded.refusals.append(_refuse(spec.name, f"missing {', '.join(missing)}"))
            continue
        record = json.loads((folder / "arm.json").read_text(encoding="utf-8"))
        points = _points(folder / "equity.csv")
        reasons = _own_reasons(spec, manifest, record, points)
        loaded.refusals.extend(_refuse(spec.name, reason) for reason in reasons)
        loaded.records[spec.name] = record
        loaded.arms[spec.name] = ArmSeries(
            spec.name, points, _closes(folder / "benchmark.csv")
        )
        summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
        loaded.absent_inputs[spec.name] = summary.get("absent_inputs", {})
    loaded.refusals.extend(_belong_together(loaded))
    return loaded


def _own_reasons(
    spec: ArmSpec, manifest: Manifest, record: dict[str, Any], points: tuple[Point, ...]
) -> list[str]:
    expected = {
        "arm": spec.name,
        "experiment": manifest.experiment,
        "overrides": list(spec.overrides),
        "require_history": manifest.require_history,
        "slippage_bps": spec.slippage_bps,
        "start": manifest.start.isoformat(),
    }
    reasons = [
        f"{key} is {record.get(key)!r}; the manifest says {value!r}"
        for key, value in expected.items()
        if record.get(key) != value
    ]
    if record.get("dirty") is not False:
        reasons.append("it ran from a worktree with uncommitted changes")
    dates = [point[0].isoformat() for point in points]
    seen = (len(dates), dates[0] if dates else None, dates[-1] if dates else None)
    told = (
        record.get("sessions"),
        record.get("first_session"),
        record.get("last_session"),
    )
    if seen != told:
        reasons.append(f"equity.csv holds {seen}; arm.json records {told}")
    return reasons


def _belong_together(loaded: LoadedArms) -> list[dict[str, str]]:
    if not loaded.arms:
        return []
    reference = BASE_ARM if BASE_ARM in loaded.arms else next(iter(loaded.arms))
    ref_record, ref_arm = loaded.records[reference], loaded.arms[reference]
    refusals: list[dict[str, str]] = []
    for name, arm in loaded.arms.items():
        if name == reference:
            continue
        record = loaded.records[name]
        for key, label in _SHARED:
            if record.get(key) != ref_record.get(key):
                refusals.append(_refuse(name, f"its {label} from {reference}'s"))
        if [p[0] for p in arm.points] != [p[0] for p in ref_arm.points]:
            refusals.append(_refuse(name, f"its sessions differ from {reference}'s"))
        if arm.closes != ref_arm.closes:
            refusals.append(_refuse(name, f"its SPY closes differ from {reference}'s"))
    return refusals


def _points(path: Path) -> tuple[Point, ...]:
    with path.open(encoding="utf-8", newline="") as handle:
        return tuple(
            (
                date.fromisoformat(row["date"]),
                int(row["equity_cents"]),
                int(row["long_cents"]),
            )
            for row in csv.DictReader(handle)
        )


def _closes(path: Path) -> dict[date, float]:
    with path.open(encoding="utf-8", newline="") as handle:
        return {
            date.fromisoformat(row["date"]): float(row["close"])
            for row in csv.DictReader(handle)
        }


def _refuse(arm: str, reason: str) -> dict[str, str]:
    return {"arm": arm, "reason": reason}
