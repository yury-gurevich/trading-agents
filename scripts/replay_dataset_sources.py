"""The two feeds behind the replay dataset, and the universe they cover.

Agent: tooling
Role: fetch Cboe VIX history and Alpaca adjusted daily bars for the live universe.
External I/O: Cboe CSV (keyless), Alpaca market data (keyed), the graph.

Split out of replay_dataset.py by the chore that taught the size gate to read
`scripts/` - that file was 205 lines and nothing objected, which was the defect.
"""

from __future__ import annotations

import csv
import io
import os
import time
from typing import Any

import requests

VIX_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"
BARS_URL = "https://data.alpaca.markets/v2/stocks/bars"
START = "2016-01-01"


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
        resolved_run_id = str(run_id or "")
        if market is not None and resolved_run_id.startswith("sched-"):
            return resolved_run_id, sorted({bar.ticker.upper() for bar in market.bars})
    raise RuntimeError("no scheduled run with a MarketData snapshot")


def daily_bars(
    tickers: list[str], end: str, timeout: int = 60, start: str = START
) -> dict[str, list[Any]]:
    """Return split- and dividend-adjusted SIP daily bars per ticker."""
    headers = {
        "APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"],
        "APCA-API-SECRET-KEY": os.environ["ALPACA_API_SECRET"],
    }
    bars: dict[str, list[Any]] = {}
    token = None
    while True:
        params: dict[str, str | int] = {
            "symbols": ",".join(tickers),
            "timeframe": "1Day",
            "start": start,
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
        raw_token = body.get("next_page_token")
        token = str(raw_token) if raw_token else None
        if not token:
            return bars
        time.sleep(0.3)
