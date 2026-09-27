"""Shared helpers for the S237 fidelity tests.

Agent: tooling
Role: export fleet graphs, build tiny git repos and caches, and read report files.
External I/O: local tmp files and a local git binary only.
"""

from __future__ import annotations

import csv
import gzip
import io
import json
import os
import shutil
import subprocess
from typing import TYPE_CHECKING, Any

from scripts.fidelity_exporter import export_sessions
from scripts.replay_fidelity_compare import run_fidelity
from scripts.replay_universe_cache import write_universe_cache
from scripts.sp500_bars import BarRow
from scripts.sp500_membership import Episode, MembershipResult
from tests.fidelity_fleet_data import (
    CALENDAR,
    SESSIONS,
    TICKERS,
    close,
    sip_volume,
    spy_bar,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import date
    from pathlib import Path

    from kernel import GraphStore

_GIT_ENV = {
    "GIT_AUTHOR_DATE": "2026-09-01T00:00:00+00:00",
    "GIT_COMMITTER_DATE": "2026-09-01T00:00:00+00:00",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
}


def git(repo: Path, *args: str) -> str:
    """Run one git command in ``repo`` with an isolated, fixed-date config."""
    binary = shutil.which("git") or "git"
    result = subprocess.run(  # noqa: S603 - fixed git binary over a tmp repo.
        [
            binary,
            "-c",
            "user.name=fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "init.defaultBranch=main",
            "-C",
            str(repo),
            *args,
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, **_GIT_ENV},
    )
    return result.stdout.strip()


def tiny_repo(path: Path, *, changed: tuple[str, ...] = ()) -> tuple[Path, str]:
    """Return a repo and its deploy SHA; HEAD then changes the ``changed`` paths."""
    path.mkdir(parents=True)
    git(path, "init", "-q")
    (path / "README.md").write_text("deploy\n", encoding="utf-8")
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", "deploy")
    deploy = git(path, "rev-parse", "HEAD")
    for name in changed:
        target = path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("changed after the deploy\n", encoding="utf-8")
    if changed:
        git(path, "add", "-A")
        git(path, "commit", "-q", "-m", "after the deploy")
    return path, deploy


def export(graph: GraphStore, out: Path) -> Path:
    """Export every fixture session through the real exporter."""
    export_sessions(graph, start=SESSIONS[0], end=SESSIONS[-1], out=out)
    return out


def copy_export(source: Path, target: Path) -> Path:
    """Return a private copy of an export directory a test may edit."""
    shutil.copytree(source, target)
    return target


def edit_session(
    export_dir: Path, session: date, change: Callable[[dict[str, Any]], None]
) -> None:
    """Apply ``change`` to one exported session file in place."""
    path = export_dir / f"sched-{session.isoformat()}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    change(payload)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def replay(
    export_dir: Path, out: Path, repo: Path, cache: Path | None = None
) -> dict[str, Any]:
    """Run the fidelity replay with the tiny repo as git evidence."""
    return run_fidelity(export=export_dir, cache=cache, out=out, repo=repo)


def rows(out: Path, name: str = "layer1.csv") -> list[dict[str, str]]:
    """Read one report CSV."""
    with (out / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def differences(out: Path) -> list[dict[str, str]]:
    """Return Layer 1 rows that did not match."""
    return [row for row in rows(out) if row["match"] != "True"]


def write_cache(path: Path, lines: tuple[str, ...] = TICKERS) -> Path:
    """Write an S235 cache holding the fixture's bars with SIP volume."""
    path.mkdir(parents=True)
    days = CALENDAR
    membership = MembershipResult(
        episodes=tuple(Episode(line, line, days[0], days[-1]) for line in lines),
        members_by_session=dict.fromkeys(days, lines),
        unreconciled=(),
        count_min=len(lines),
        count_max=len(lines),
    )
    bars = tuple(
        BarRow(
            line,
            line,
            day,
            round(close(line, day) * 0.995, 4),
            round(close(line, day) * 1.01, 4),
            round(close(line, day) * 0.99, 4),
            close(line, day),
            sip_volume(line, day),
        )
        for line in lines
        for day in days
    )
    write_universe_cache(path, days, membership, bars, {})
    spy = tuple(spy_bar(day) for day in days)
    _csv_gz(
        path / "sp500_benchmark.csv.gz",
        ["symbol", "date", "open", "high", "low", "close", "volume"],
        [
            ["SPY", bar.bar_date, bar.open, bar.high, bar.low, bar.close, bar.volume]
            for bar in spy
        ],
    )
    _csv_gz(path / "sp500_vix.csv.gz", ["date", "vix_close"], [[days[-1], 18]])
    return path


def _csv_gz(path: Path, header: list[str], body: list[list[object]]) -> None:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(body)
    path.write_bytes(gzip.compress(buffer.getvalue().encode("utf-8")))
