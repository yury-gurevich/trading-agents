"""Shared price_cache CSV loader for offline forecaster scripts.

Agent: tooling
Role: read price_cache CSV exports into ticker-sorted close/volume bar series.
External I/O: filesystem (reads CSV exports).
"""

from __future__ import annotations

import csv
from pathlib import Path


def load_price_csv(path: str) -> dict[str, list[tuple[str, float, float]]]:
    """Read price_cache CSV into {ticker: [(date, close, volume), ...]}."""
    ticker_bars: dict[str, list[tuple[str, float, float]]] = {}
    with Path(path).open(newline="") as fh:
        for row in csv.DictReader(fh):
            ticker = row["ticker"]
            ticker_bars.setdefault(ticker, []).append(
                (row["date"], float(row["close"]), float(row["volume"]))
            )
    for bars in ticker_bars.values():
        bars.sort(key=lambda t: t[0])
    return ticker_bars
