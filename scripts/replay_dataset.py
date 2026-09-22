"""Build and cache the replay dataset the sizing/regime experiments run on.

Agent: tooling
Role: fetch VIX history and adjusted daily bars once, then serve them from a cache.
External I/O: Cboe CSV (keyless), Alpaca market data (keyed), the graph, local cache.

EXP-011 and EXP-012 each carried their loader as a markdown appendix and left the
dataset in a scratch directory. Both were gone when EXP-013 needed them, so the
bars had to be re-pulled from Alpaca to reproduce a published number. The code
lives here now, and the cache survives between runs.

🚨 The cache holds Alpaca SIP consolidated-tape bars. This repository is public
and that data is licensed, so the cache path is deliberately OUTSIDE the worktree
and the file is never committed. Do not add it to the repo or to a release asset.

    uv run python scripts/replay_dataset.py            # build or refresh the cache
    uv run python scripts/replay_dataset.py --describe # report what is cached
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

VIX_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"
BARS_URL = "https://data.alpaca.markets/v2/stocks/bars"
START = "2016-01-01"


def _cache_dir() -> Path:
    """Prefer a synced cloud folder, so the dataset survives this machine."""
    override = os.environ.get("REPLAY_DATASET_DIR")
    if override:
        return Path(override)
    for parent in (Path.home() / "OneDrive", Path.home() / "Google Drive"):
        if parent.is_dir():
            return parent / "trading-agents-data"
    return Path.home() / ".trading-agents-data"


CACHE = _cache_dir()


def vix_history(timeout: int = 60) -> dict[str, float]:
    """Return Cboe's daily VIX closes, keyed YYYY-MM-DD. No key required."""
    response = requests.get(VIX_URL, timeout=timeout)
    response.raise_for_status()
    closes: dict[str, float] = {}
    for row in csv.DictReader(io.StringIO(response.text)):
        month, day, year = row["DATE"].split("/")
        closes[f"{year}-{int(month):02d}-{int(day):02d}"] = float(row["CLOSE"])
    return closes


def live_universe() -> tuple[str, list[str]]:
    """Return the run id and tickers of the latest scheduled run's snapshot."""
    from agents.portfolio_manager.poll import _market_and_regime
    from kernel.graph_env import build_graph_from_env

    graph = build_graph_from_env()
    runs = sorted(
        graph.list_nodes("AnalystRun"),
        key=lambda node: str(node.props.get("created_at")),
    )
    for analyst_run in reversed(runs):
        market, _regime, run_id = _market_and_regime(graph, analyst_run)
        if market is not None and run_id.startswith("sched-"):
            return run_id, sorted({bar.ticker.upper() for bar in market.bars})
    raise RuntimeError("no scheduled run with a MarketData snapshot")


def daily_bars(tickers: list[str], end: str, timeout: int = 60) -> dict[str, list[Any]]:
    """Return split- and dividend-adjusted SIP daily bars per ticker."""
    headers = {
        "APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"],
        "APCA-API-SECRET-KEY": os.environ["ALPACA_API_SECRET"],
    }
    bars: dict[str, list[Any]] = {}
    token = None
    while True:
        params = {
            "symbols": ",".join(tickers),
            "timeframe": "1Day",
            "start": START,
            "end": end,
            "adjustment": "all",
            "feed": "sip",
            "limit": 10000,
        }
        if token:
            params["page_token"] = token
        response = requests.get(
            BARS_URL, headers=headers, params=params, timeout=timeout
        )
        response.raise_for_status()
        body = response.json()
        for symbol, rows in (body.get("bars") or {}).items():
            bars.setdefault(symbol, []).extend(
                (row["t"][:10], row["o"], row["h"], row["l"], row["c"]) for row in rows
            )
        token = body.get("next_page_token")
        if not token:
            return bars
        time.sleep(0.3)


def _write(path: Path, header: list[str], rows: list[list[Any]]) -> int:
    import gzip

    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    path.write_bytes(gzip.compress(buffer.getvalue().encode("utf-8"), 9))
    return len(rows)


def build(end: str) -> None:
    """Fetch both sources and write the cache as gzipped CSV."""
    CACHE.mkdir(parents=True, exist_ok=True)
    run_id, tickers = live_universe()
    print(f"universe {run_id}: {len(tickers)} tickers")
    closes = vix_history()
    count = _write(
        CACHE / "vix.csv.gz",
        ["date", "vix_close"],
        [[day, closes[day]] for day in sorted(closes)],
    )
    print(f"vix: {count:,} sessions -> {CACHE / 'vix.csv.gz'}")
    bars = daily_bars(tickers, end)
    rows = [[symbol, *row] for symbol in sorted(bars) for row in sorted(bars[symbol])]
    count = _write(
        CACHE / "bars.csv.gz",
        ["ticker", "date", "open", "high", "low", "close"],
        rows,
    )
    print(f"bars: {count:,} rows, {len(bars)} names -> {CACHE / 'bars.csv.gz'}")


_Bars = dict[str, list[tuple[str, float, float, float, float]]]


def load() -> tuple[dict[str, float], _Bars]:
    """Read the cache. Raises if it has not been built."""
    import gzip

    vix_path, bars_path = CACHE / "vix.csv.gz", CACHE / "bars.csv.gz"
    if not vix_path.exists() or not bars_path.exists():
        message = f"no cache in {CACHE}; run scripts/replay_dataset.py first"
        raise FileNotFoundError(message)
    vix_text = gzip.decompress(vix_path.read_bytes()).decode()
    closes = {
        row["date"]: float(row["vix_close"])
        for row in csv.DictReader(io.StringIO(vix_text))
    }
    bars: _Bars = {}
    bars_text = gzip.decompress(bars_path.read_bytes()).decode()
    for row in csv.DictReader(io.StringIO(bars_text)):
        bars.setdefault(row["ticker"], []).append(
            (
                row["date"],
                float(row["open"]),
                float(row["high"]),
                float(row["low"]),
                float(row["close"]),
            )
        )
    return closes, bars


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Build or describe the replay cache.")
    parser.add_argument(
        "--describe", action="store_true", help="report the cache, do not fetch"
    )
    parser.add_argument("--end", default="2026-09-16T23:59:00Z", help="bar window end")
    arguments = parser.parse_args(argv)
    load_dotenv(_ROOT / ".env")
    if arguments.describe:
        closes, bars = load()
        rows = sum(len(v) for v in bars.values())
        dates = sorted(d for v in bars.values() for d, *_ in v)
        print(f"cache: {CACHE}")
        print(f"  vix  {len(closes):,} sessions {min(closes)} -> {max(closes)}")
        print(f"  bars {rows:,} rows, {len(bars)} names, {dates[0]} -> {dates[-1]}")
        return 0
    build(arguments.end)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
