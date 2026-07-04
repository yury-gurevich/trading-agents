"""Export Tiingo daily bars into the offline forecaster CSV format.

Agent: tooling
Role: fetch paced, resumable Tiingo EOD bars through the in-tree provider client.
External I/O: reads .env/ticker files, calls Tiingo HTTPS, writes a CSV export.

Mandatory before live Tiingo use: read docs/laws/tiingo-usage-limits.md.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError

# Keep sys.path clean: run from the repo root so the package is importable.
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.tiingo_export_retry import DEFAULT_BACKOFF_SECONDS, fetch_with_backoff

from agents.provider.tiingo import TiingoDataSource
from contracts.common import Window

DEFAULT_PACE_SECONDS = 72.0
DEFAULT_TICKERS = "scripts/universe_s110_tiingo_100.txt"


def load_env(path: Path) -> dict[str, str]:
    """Read simple KEY=VALUE entries from an env file."""
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_tickers(path: str) -> tuple[str, ...]:
    """Load non-comment ticker symbols from a one-symbol-per-line file."""
    tickers: list[str] = []
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            tickers.append(line)
    return tuple(tickers)


def completed_tickers(path: str) -> set[str]:
    """Return tickers already present in an output CSV."""
    csv_path = Path(path)
    if not csv_path.exists():
        return set()
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return {row["ticker"] for row in csv.DictReader(handle)}


def start_for_years(*, today: date, years: int) -> date:
    """Return a conservative calendar start date for a years-back export."""
    return today - timedelta(days=years * 366)


def append_bars(path: str, ticker: str, bars: list[tuple[str, float, float]]) -> None:
    """Append date-ascending bars to the trainer CSV."""
    csv_path = Path(path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    first_write = not csv_path.exists()
    with csv_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if first_write:
            writer.writerow(["date", "ticker", "close", "volume"])
        writer.writerows(
            (bar_date, ticker, close, volume) for bar_date, close, volume in bars
        )


def source_from_env(env: dict[str, str]) -> TiingoDataSource:
    """Build the Tiingo source from env values."""
    api_key = env.get("TIINGO_API_KEY") or os.environ.get("TIINGO_API_KEY", "")
    if not api_key:
        raise ValueError("TIINGO_API_KEY missing")
    return TiingoDataSource(
        api_key=api_key,
        base_url=env.get("TIINGO_BASE_URL", "https://api.tiingo.com"),
        timeout=int(env.get("TIINGO_TIMEOUT", "15")),
    )


def export_bars(
    source: TiingoDataSource,
    tickers: tuple[str, ...],
    *,
    out: str,
    window: Window,
    pace_seconds: float,
    max_requests: int | None = None,
    max_retries: int = 2,
    backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
) -> int:
    """Fetch missing tickers and append them to out; return new successful exports."""
    done = completed_tickers(out)
    successes = 0
    requests = 0
    for ticker in tickers:
        if ticker in done:
            continue
        if max_requests is not None and requests >= max_requests:
            break
        try:
            fetched = fetch_with_backoff(
                source,
                ticker,
                window,
                max_retries=max_retries,
                backoff_seconds=backoff_seconds,
            )
            requests += 1
        except HTTPError as exc:
            print(f"skip {ticker}: HTTP {exc.code}")
            if exc.code == 429:
                break
            continue
        except (TimeoutError, URLError) as exc:
            print(f"skip {ticker}: {type(exc).__name__}")
            continue
        bars = sorted(
            [
                (bar.bar_date.isoformat(), bar.close, float(bar.volume))
                for bar in fetched
            ],
            key=lambda item: item[0],
        )
        if not bars:
            print(f"skip {ticker}: no bars")
            continue
        append_bars(out, ticker, bars)
        done.add(ticker)
        successes += 1
        print(f"ok {ticker}: {len(bars)} bars")
        time.sleep(pace_seconds)
    return successes


def build_parser() -> argparse.ArgumentParser:
    """Build the exporter CLI parser."""
    parser = argparse.ArgumentParser(description="Export Tiingo bars to CSV.")
    parser.add_argument("--tickers", default=DEFAULT_TICKERS)
    parser.add_argument("--years", type=int, default=4)
    parser.add_argument("--out", required=True)
    parser.add_argument("--pace-seconds", type=float, default=DEFAULT_PACE_SECONDS)
    parser.add_argument("--max-requests", type=int, default=None)
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument(
        "--backoff-seconds", type=float, default=DEFAULT_BACKOFF_SECONDS
    )
    return parser


def main(argv: list[str] | None = None) -> None:  # pragma: no cover
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.years < 1:
        parser.error("--years must be at least 1")
    if args.pace_seconds < 0.0:
        parser.error("--pace-seconds must be non-negative")
    if args.max_retries < 0:
        parser.error("--max-retries must be non-negative")
    if args.backoff_seconds < 0.0:
        parser.error("--backoff-seconds must be non-negative")
    env = load_env(Path(".env"))
    today = datetime.now(UTC).date()
    window = Window(start=start_for_years(today=today, years=args.years), end=today)
    successes = export_bars(
        source_from_env(env),
        load_tickers(args.tickers),
        out=args.out,
        window=window,
        pace_seconds=args.pace_seconds,
        max_requests=args.max_requests,
        max_retries=args.max_retries,
        backoff_seconds=args.backoff_seconds,
    )
    total = len(completed_tickers(args.out))
    print(f"new_exports={successes}")
    print(f"completed_tickers={total}")


if __name__ == "__main__":
    main()
