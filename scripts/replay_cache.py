"""Load S235 replay cache context files.

Agent: tooling
Role: read cached universe, benchmark, VIX, and sectors without fetching data.
External I/O: local cache files only.
"""

from __future__ import annotations

import csv
import gzip
import io
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

from scripts.replay_universe_cache import Universe, load_universe_cache

from contracts.provider import OHLCVBar

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class ReplayContext:
    universe: Universe
    benchmark: dict[date, OHLCVBar]
    spy_closes: dict[date, float]
    vix: dict[date, float]
    sectors: dict[str, str]


def load_replay_cache(cache_dir: Path) -> ReplayContext:
    """Load S235 cache files, refusing old bar caches without volume."""
    universe = load_universe_cache(cache_dir)
    if not universe.has_volume:
        raise ValueError("replay cache missing required column: volume")
    benchmark = {
        row.bar_date: row for row in _read_ohlcv(cache_dir / "sp500_benchmark.csv.gz")
    }
    return ReplayContext(
        universe,
        benchmark,
        {day: bar.close for day, bar in benchmark.items()},
        _read_vix(cache_dir / "sp500_vix.csv.gz"),
        _read_sectors(cache_dir / "sp500_sectors.csv.gz"),
    )


def _read_ohlcv(path: Path) -> tuple[OHLCVBar, ...]:
    return tuple(
        OHLCVBar(
            ticker=row.get("line") or row["symbol"],
            bar_date=date.fromisoformat(row["date"]),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=int(row["volume"]),
        )
        for row in _read_rows(path)
    )


def _read_vix(path: Path) -> dict[date, float]:
    return {
        date.fromisoformat(row["date"]): float(row["vix_close"])
        for row in _read_rows(path)
    }


def _read_sectors(path: Path) -> dict[str, str]:
    return (
        {row["line"]: row["sector"] for row in _read_rows(path)}
        if path.exists()
        else {}
    )


def _read_rows(path: Path) -> list[dict[str, str]]:
    text = gzip.decompress(path.read_bytes()).decode()
    return list(csv.DictReader(io.StringIO(text)))
