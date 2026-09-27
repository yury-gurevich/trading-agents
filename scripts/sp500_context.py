"""Build S235 benchmark, VIX, sector, and cache description files.

Agent: tooling
Role: write replay context artifacts beside the S&P 500 membership cache.
External I/O: Alpaca/Cboe/Finnhub through injected or real callables.
"""

from __future__ import annotations

import csv
import gzip
import io
import os
import time
from collections.abc import Callable, Iterable
from datetime import date
from typing import TYPE_CHECKING, Any

import requests
from scripts.replay_dataset_sources import daily_bars, vix_history
from scripts.replay_universe_cache import load_universe_cache

from agents.provider.fundamentals_parse import _parse_sector

if TYPE_CHECKING:
    from pathlib import Path

BENCHMARK_SYMBOL = "SPY"
FINNHUB_PROFILE_URL = "https://finnhub.io/api/v1/stock/profile2"
FINNHUB_PACE_SECONDS = 1.0

BarFetcher = Callable[..., dict[str, list[Any]]]
VixFetcher = Callable[[], dict[str, float]]
GetText = Callable[..., str]
Sleeper = Callable[[float], None]


def build_context_files(
    cache_dir: Path,
    sessions: tuple[date, ...],
    bar_fetcher: BarFetcher = daily_bars,
    vix_fetcher: VixFetcher = vix_history,
) -> None:
    """Write SPY benchmark and VIX files for exactly the cached sessions."""
    if not sessions:
        _write_csv(cache_dir / "sp500_benchmark.csv.gz", _benchmark_header(), [])
        _write_csv(cache_dir / "sp500_vix.csv.gz", ["date", "vix_close"], [])
        return
    start, end = sessions[0].isoformat(), sessions[-1].isoformat()
    benchmark = bar_fetcher(
        [BENCHMARK_SYMBOL],
        start=start,
        end=end,
        asof=end,
        adjustment="all",
        with_volume=True,
    ).get(BENCHMARK_SYMBOL, ())
    session_set = set(sessions)
    _write_csv(
        cache_dir / "sp500_benchmark.csv.gz",
        _benchmark_header(),
        [
            _benchmark_row(raw)
            for raw in benchmark
            if date.fromisoformat(str(raw[0])[:10]) in session_set
        ],
    )
    vix = vix_fetcher()
    _write_csv(
        cache_dir / "sp500_vix.csv.gz",
        ["date", "vix_close"],
        [
            [day.isoformat(), vix[day.isoformat()]]
            for day in sessions
            if day.isoformat() in vix
        ],
    )


def fetch_sectors(
    cache_dir: Path,
    symbols: Iterable[str | tuple[str, str]],
    *,
    api_key: str | None = None,
    get: GetText | None = None,
    sleep: Sleeper = time.sleep,
    timeout: int = 15,
) -> tuple[tuple[str, str, str], ...]:
    """Fetch Finnhub sectors once per distinct symbol, preserving line mapping."""
    key = api_key or os.environ["PROVIDER_FINNHUB_API_KEY"]  # the fleet's name
    rows = tuple(sorted({_line_symbol(item) for item in symbols}))
    sectors: dict[str, str] = {}
    client = get or _requests_get_text
    for index, symbol in enumerate(sorted({symbol for _line, symbol in rows})):
        if index:
            sleep(FINNHUB_PACE_SECONDS)
        raw = client(
            FINNHUB_PROFILE_URL,
            params={"symbol": symbol, "token": key},
            timeout=timeout,
        )
        sectors[symbol] = _parse_sector(raw) or ""
    out = tuple((line, symbol, sectors[symbol]) for line, symbol in rows)
    _write_csv(cache_dir / "sp500_sectors.csv.gz", ["line", "symbol", "sector"], out)
    return out


def build_sector_file(cache_dir: Path) -> tuple[tuple[str, str, str], ...]:
    """Write sectors for every distinct line/symbol in the cached membership."""
    universe = load_universe_cache(cache_dir)
    return fetch_sectors(
        cache_dir,
        sorted({(episode.line, episode.ticker) for episode in universe.episodes}),
    )


def describe_cache(cache_dir: Path) -> str:
    """Describe the replay universe and S235 context coverage."""
    universe = load_universe_cache(cache_dir)
    reconciliation = universe.coverage["reconciliation"]
    coverage = universe.coverage["coverage"]
    lines = [
        f"cache: {cache_dir}",
        (
            "membership: "
            f"{len(universe.episodes)} episodes, count "
            f"{reconciliation['count_min']}..{reconciliation['count_max']}, "
            f"unreconciled {len(reconciliation['unreconciled'])}"
        ),
        (
            "coverage: "
            f"{coverage['covered_sessions']}/{coverage['member_sessions']} "
            f"({coverage['ratio']:.2%}), shortfalls {len(coverage['shortfalls'])}"
        ),
        f"volume: {'present' if universe.has_volume else 'missing'}",
        _file_span("benchmark sessions", cache_dir / "sp500_benchmark.csv.gz"),
        _file_span("VIX range", cache_dir / "sp500_vix.csv.gz"),
        _sector_coverage(cache_dir / "sp500_sectors.csv.gz"),
    ]
    return "\n".join(lines)


def _benchmark_header() -> list[str]:
    return ["symbol", "date", "open", "high", "low", "close", "volume"]


def _benchmark_row(raw: tuple[object, ...]) -> list[object]:
    day, open_, high, low, close, *rest = raw
    volume = rest[0] if rest else 0
    return [BENCHMARK_SYMBOL, day, open_, high, low, close, volume]


def _requests_get_text(url: str, *, params: dict[str, str], timeout: int) -> str:
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return str(response.text)


def _line_symbol(item: str | tuple[str, str]) -> tuple[str, str]:
    if isinstance(item, tuple):
        return item
    return item, item


def _file_span(label: str, path: Path) -> str:
    if not path.exists():
        return f"{label}: missing"
    rows = _read_rows(path)
    if not rows:
        return f"{label}: 0"
    dates = [row["date"] for row in rows]
    return f"{label}: {len(rows)} ({min(dates)}..{max(dates)})"


def _sector_coverage(path: Path) -> str:
    if not path.exists():
        return "sector coverage: missing"
    rows = _read_rows(path)
    covered = sum(1 for row in rows if row.get("sector"))
    return f"sector coverage: {covered}/{len(rows)}"


def _write_csv(path: Path, header: list[str], rows: Iterable[Iterable[Any]]) -> None:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    path.write_bytes(gzip.compress(buffer.getvalue().encode("utf-8"), 9))


def _read_rows(path: Path) -> list[dict[str, str]]:
    return list(
        csv.DictReader(io.StringIO(gzip.decompress(path.read_bytes()).decode()))
    )
