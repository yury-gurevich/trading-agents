"""What an EXP-014 arm ran on: commit, worktree state, cache checksums, sessions (S250).

Agent: tooling
Role: read the repo state and the cache's identity, and write an arm's SPY closes.
External I/O: runs the local `git` binary read-only; reads cache files; writes one CSV.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from scripts.replay_fidelity_git import _git

_ROOT = Path(__file__).resolve().parents[1]
# Every file `load_replay_cache` reads (DL-258 D4); sectors alone is optional.
CACHE_FILES = (
    "sp500_bars.csv.gz",
    "sp500_benchmark.csv.gz",
    "sp500_coverage.json",
    "sp500_membership.csv.gz",
    "sp500_sectors.csv.gz",
    "sp500_sessions.csv.gz",
    "sp500_vix.csv.gz",
)
CHECKSUM_HEX = 12  # EXP-014 section 3 records 12-hex SHA-256 prefixes
ABSENT = "absent"


@dataclass(frozen=True)
class RepoState:
    """The commit an arm ran on and whether tracked files differed from it."""

    commit: str
    dirty: bool


def read_repo_state(repo: Path = _ROOT) -> RepoState:
    """`git rev-parse HEAD` and `git status --porcelain --untracked-files=no`."""
    commit = _git(repo, "rev-parse", "HEAD")[0]
    changes = _git(repo, "status", "--porcelain", "--untracked-files=no")
    return RepoState(commit, bool(changes))


def cache_checksums(cache_dir: Path) -> dict[str, str]:
    """A SHA-256 prefix per cache file the harness reads; a missing one is `absent`."""
    out: dict[str, str] = {}
    for name in CACHE_FILES:
        path = cache_dir / name
        out[name] = (
            hashlib.sha256(path.read_bytes()).hexdigest()[:CHECKSUM_HEX]
            if path.exists()
            else ABSENT
        )
    return out


def equity_dates(path: Path) -> tuple[date, ...]:
    """The sessions a replay's `equity.csv` holds, in order."""
    with path.open(encoding="utf-8", newline="") as handle:
        return tuple(date.fromisoformat(row["date"]) for row in csv.DictReader(handle))


def write_benchmark(cache_dir: Path, sessions: tuple[date, ...], out: Path) -> None:
    """Write the cache's SPY close for each of the arm's sessions (date, close)."""
    text = gzip.decompress((cache_dir / "sp500_benchmark.csv.gz").read_bytes())
    closes = {
        row["date"]: row["close"]
        for row in csv.DictReader(io.StringIO(text.decode("utf-8")))
    }
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["date", "close"])
        for day in sessions:
            key = day.isoformat()
            if key in closes:
                writer.writerow([key, repr(float(closes[key]))])
