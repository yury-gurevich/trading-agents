"""Invented EXP-022 arms and replay folders for the S282 proof.

Agent: tooling
Role: plant session drifts on one SPY walk and write faithful arm folders.
External I/O: local temporary files only; no market data or network.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

from scripts.exit_verdict_rule import expected_arms
from scripts.replay_arms import load_manifest
from scripts.replay_verdict_score import ArmSeries
from tests.replay_arm_folders import edit_record, read_record, write_arm
from tests.replay_verdict_fixtures import (
    EXPOSURE,
    spy_closes,
    synthetic_arm,
    trading_days,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from scripts.replay_arms import Manifest

STEMS = ("stops", "target", "time10", "trail", "target-time10", "cool5")
ARM_NAMES = tuple(f"{stem}-{bps}" for bps in (25, 10) for stem in STEMS)
FILL_HEADER = ("date", "line", "side", "quantity", "price_cents", "reason")
Drift = float | tuple[float, float]


def twelve_arms(
    drifts: Mapping[str, Drift] | None = None, *, count: int = 301
) -> dict[str, ArmSeries]:
    """Each challenger copies its own family's noisy champion plus a planted drift."""
    assert expected_arms() == ARM_NAMES
    closes = spy_closes(trading_days(date(2017, 1, 3), count))
    arms = {}
    for bps, drift, seed in ((25, 0.0, 11), (10, 0.0002, 17)):
        base = synthetic_arm(f"stops-{bps}", closes, drift=drift, seed=seed)
        arms[base.name] = base
        for stem in STEMS[1:]:
            name = f"{stem}-{bps}"
            arms[name] = shifted_halves(base, name, (drifts or {}).get(name, 0.0))
    return arms


def shifted_halves(arm: ArmSeries, name: str, drift: Drift) -> ArmSeries:
    """Add drift to each step, switching exactly at the shared middle point."""
    halves = drift if isinstance(drift, tuple) else (drift, drift)
    equity, points = arm.points[0][1], [arm.points[0]]
    middle = (len(arm.points) - 1) // 2
    for index, (before, after) in enumerate(
        zip(arm.points, arm.points[1:], strict=False)
    ):
        equity = round(equity * (after[1] / before[1] + halves[index >= middle]))
        points.append((after[0], equity, round(EXPOSURE * equity)))
    return ArmSeries(name, tuple(points), dict(arm.closes))


def write_rows(path: Path, rows: Sequence[dict[str, str]]) -> None:
    """Fill rows in replay file order, with the replay's column names."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FILL_HEADER, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def fill(
    day: date, line: str, side: str, price: int, reason: str = "limit"
) -> dict[str, str]:
    """One integer-cent, one-share invented fill."""
    return dict(
        zip(
            FILL_HEADER,
            (day.isoformat(), line, side, "1", str(price), reason),
            strict=True,
        )
    )


def trip_rows(days: Sequence[date]) -> list[dict[str, str]]:
    """Five buys, four FIFO trips, one stray sell and one buy left open."""
    return [
        fill(days[0], "same", "buy", 10_000),
        fill(days[1], "same", "buy", 20_000),
        fill(days[2], "same", "sell", 9_000, "stop"),
        fill(days[3], "timed", "buy", 10_000),
        fill(days[13], "timed", "sell", 10_000, "time_exit"),
        fill(days[15], "same", "sell", 22_000, "take_profit"),
        fill(days[16], "same", "buy", 10_000),
        fill(days[20], "same", "sell", 11_000, "take_profit"),
        fill(days[21], "stray", "sell", 10_000, "stop"),
        fill(days[22], "open", "buy", 10_000),
    ]


def write_arms(
    root: Path,
    drifts: Mapping[str, Drift] | None = None,
    *,
    count: int = 121,
    manifest: Manifest | None = None,
) -> Path:
    """Twelve folders, each with two complete trips and S250's provenance fields."""
    manifest = manifest or load_manifest(
        Path(__file__).resolve().parents[1] / "scripts/exp022_arms.json"
    )
    arms = twelve_arms(drifts, count=count)
    for spec in manifest.arms:
        arm = arms[spec.name]
        write_arm(root, arm, spec.slippage_bps, list(spec.overrides))
        folder, days = root / spec.name, [point[0] for point in arm.points]
        record = read_record(folder)
        record.update(
            experiment=manifest.experiment,
            start=manifest.start.isoformat(),
            require_history=manifest.require_history,
        )
        if spec.exits.declared:
            record["exits"] = spec.exits.as_dict()
        edit_record(folder, record)
        write_rows(
            folder / "fills.csv",
            [
                fill(days[0], "first", "buy", 10_000),
                fill(days[2], "first", "sell", 9_000, "stop"),
                fill(days[3], "next", "buy", 10_000),
                fill(days[13], "next", "sell", 11_000, "take_profit"),
            ],
        )
    return root
