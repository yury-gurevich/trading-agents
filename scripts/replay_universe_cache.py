"""Cache serialization for the S231 S&P 500 replay universe.

Agent: tooling
Role: read and write replay-universe cache files without fetching data.
External I/O: local cache files outside the repository worktree.
"""

from __future__ import annotations

import csv
import gzip
import io
import json
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Any, cast

from scripts.sp500_bars import BarRow
from scripts.sp500_membership import Episode

if TYPE_CHECKING:
    from pathlib import Path

    from scripts.sp500_bars import BarWindow
    from scripts.sp500_coverage import CoverageReport
    from scripts.sp500_membership import MembershipResult


@dataclass(frozen=True)
class Universe:
    sessions: tuple[date, ...]
    episodes: tuple[Episode, ...]
    bars: tuple[BarRow, ...]
    coverage: dict[str, Any]


def write_pages(cache_dir: Path, pages: dict[str, dict[str, str]]) -> None:
    payload = {"fetched_at": datetime.now(UTC).isoformat(), "pages": pages}
    (cache_dir / "sp500_pages.json.gz").write_bytes(
        gzip.compress(json.dumps(payload).encode())
    )


def load_pages(cache_dir: Path) -> dict[str, dict[str, str]]:
    payload = json.loads(
        gzip.decompress((cache_dir / "sp500_pages.json.gz").read_bytes())
    )
    return cast("dict[str, dict[str, str]]", payload["pages"])


def write_universe_cache(
    cache_dir: Path,
    sessions: tuple[date, ...],
    membership: MembershipResult,
    bars: tuple[BarRow, ...],
    coverage: dict[str, Any],
) -> None:
    _write_csv(
        cache_dir / "sp500_sessions.csv.gz", ["date"], [[day] for day in sessions]
    )
    _write_csv(
        cache_dir / "sp500_membership.csv.gz",
        ["line", "ticker", "first", "last"],
        [[row.line, row.ticker, row.first, row.last] for row in membership.episodes],
    )
    _write_csv(
        cache_dir / "sp500_bars.csv.gz",
        ["line", "symbol", "date", "open", "high", "low", "close"],
        [
            [row.line, row.symbol, row.date, row.open, row.high, row.low, row.close]
            for row in bars
        ],
    )
    (cache_dir / "sp500_coverage.json").write_text(
        json.dumps(coverage, default=str, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def load_universe_cache(cache_dir: Path) -> Universe:
    sessions = tuple(
        date.fromisoformat(row["date"])
        for row in _read_csv(cache_dir / "sp500_sessions.csv.gz")
    )
    episodes = tuple(
        Episode(
            row["line"],
            row["ticker"],
            date.fromisoformat(row["first"]),
            date.fromisoformat(row["last"]),
        )
        for row in _read_csv(cache_dir / "sp500_membership.csv.gz")
    )
    bars = tuple(
        BarRow(
            row["line"],
            row["symbol"],
            date.fromisoformat(row["date"]),
            float(row["open"]),
            float(row["high"]),
            float(row["low"]),
            float(row["close"]),
        )
        for row in _read_csv(cache_dir / "sp500_bars.csv.gz")
    )
    coverage = json.loads(
        (cache_dir / "sp500_coverage.json").read_text(encoding="utf-8")
    )
    return Universe(sessions, episodes, bars, coverage)


def coverage_payload(
    report: CoverageReport,
    membership: MembershipResult,
    refetched: tuple[BarWindow, ...],
) -> dict[str, Any]:
    return {
        "coverage": {**asdict(report), "ratio": report.ratio},
        "reconciliation": {
            "count_min": membership.count_min,
            "count_max": membership.count_max,
            "unreconciled": [asdict(row) for row in membership.unreconciled],
        },
        "refetched": [asdict(window) for window in refetched],
    }


def _write_csv(path: Path, header: list[str], rows: list[list[Any]]) -> None:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    path.write_bytes(gzip.compress(buffer.getvalue().encode("utf-8"), 9))


def _read_csv(path: Path) -> tuple[dict[str, str], ...]:
    text = gzip.decompress(path.read_bytes()).decode("utf-8")
    return tuple(csv.DictReader(io.StringIO(text)))
