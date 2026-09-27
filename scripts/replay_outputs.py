"""Write deterministic S235 replay outputs.

Agent: tooling
Role: keep licensed replay artifacts outside the worktree and delegate metrics.
External I/O: local output files outside the repository worktree.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, NamedTuple

from agents.reporter.domain.performance import calculate_performance

if TYPE_CHECKING:
    from datetime import date

_ROOT = Path(__file__).resolve().parents[1]


class EquityPoint(NamedTuple):
    date: date
    equity_cents: int
    long_cents: int


def refuse_worktree_out(out: Path) -> Path:
    """Return a resolved output dir, rejecting paths inside this worktree."""
    resolved = out.resolve()
    try:
        resolved.relative_to(_ROOT.resolve())
    except ValueError:
        return out
    raise ValueError(f"replay output path is inside the worktree: {out}")


def performance_summary(
    points: tuple[EquityPoint, ...], spy_closes: dict[date, float]
) -> dict[str, float]:
    """Calculate performance exclusively through reporter domain code."""
    return calculate_performance(points, spy_closes, rolling_sessions=20)


def write_replay_outputs(
    out: Path,
    equity: tuple[EquityPoint, ...],
    fills: tuple[dict[str, Any], ...],
    sessions: tuple[dict[str, Any], ...],
    summary: dict[str, Any],
) -> None:
    """Write byte-stable replay artifacts."""
    out.mkdir(parents=True, exist_ok=True)
    _write_csv(
        out / "equity.csv",
        ["date", "equity_cents", "long_cents"],
        [
            [point.date.isoformat(), point.equity_cents, point.long_cents]
            for point in equity
        ],
    )
    _write_dict_csv(out / "fills.csv", fills)
    _write_dict_csv(out / "sessions.csv", sessions)
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_dict_csv(path: Path, rows: tuple[dict[str, Any], ...]) -> None:
    header = sorted({key for row in rows for key in row})
    _write_csv(path, header, [[row.get(key, "") for key in header] for row in rows])


def _write_csv(path: Path, header: list[str], rows: list[list[Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
