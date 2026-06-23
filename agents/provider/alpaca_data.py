"""Alpaca daily-bars source over the provider DataSource boundary.

Agent: provider
Role: fetch daily OHLCV bars from Alpaca's market-data bars endpoint in a
single multi-symbol request (the primary batch OHLCV feed — DL-16). One call
covers up to ~100 symbols, avoiding the per-symbol rate limit that 429s Tiingo.
External I/O: optional HTTPS calls to data.alpaca.markets.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import date
from typing import TYPE_CHECKING

from agents.provider.sources import RegimeInputs
from contracts.provider import OHLCVBar

if TYPE_CHECKING:
    from contracts.common import Window


class AlpacaDataSource:
    """Alpaca market-data source for daily OHLCV bars (batch multi-symbol)."""

    def __init__(
        self,
        *,
        api_key: str,
        api_secret: str,
        base_url: str,
        feed: str,
        timeout: int,
    ) -> None:
        """Create an Alpaca OHLCV source from injected settings."""
        self._api_key = api_key
        self._api_secret = api_secret
        self._base_url = base_url
        self._feed = feed
        self._timeout = timeout

    def fetch_ohlcv(
        self, tickers: tuple[str, ...], window: Window
    ) -> tuple[OHLCVBar, ...]:
        """Fetch daily OHLCV bars for all tickers in one batch, within the window."""
        if not tickers:
            return ()
        return _parse_bars(self._download(tickers, window), window)

    def fetch_regime_inputs(self, as_of: date) -> RegimeInputs:
        """Return empty regime inputs; Alpaca serves OHLCV only here."""
        return RegimeInputs(as_of=as_of, vix=None)

    def fetch_fundamentals(
        self,
        tickers: tuple[str, ...],  # noqa: ARG002 - port signature; Alpaca serves OHLCV.
        window: Window,  # noqa: ARG002 - port signature; Alpaca serves OHLCV.
    ) -> dict[str, dict[str, float]]:
        """Return no fundamentals; Alpaca serves OHLCV only here."""
        return {}

    def fetch_news(
        self,
        tickers: tuple[str, ...],  # noqa: ARG002 - port signature; Alpaca serves OHLCV.
        window: Window,  # noqa: ARG002 - port signature; Alpaca serves OHLCV.
    ) -> dict[str, tuple[str, ...]]:
        """Return no news; Alpaca serves OHLCV only here."""
        return {}

    def fetch_sentiment(
        self,
        tickers: tuple[str, ...],  # noqa: ARG002 - port signature; Alpaca serves OHLCV.
    ) -> dict[str, float]:
        """Return no sentiment; Alpaca serves OHLCV only here."""
        return {}

    def fetch_sectors(
        self,
        tickers: tuple[str, ...],  # noqa: ARG002 - port signature; Alpaca serves OHLCV.
    ) -> dict[str, str]:
        """Return no sectors; Alpaca serves OHLCV only here."""
        return {}

    def fetch_earnings(
        self,
        tickers: tuple[str, ...],  # noqa: ARG002 - port signature; Alpaca serves OHLCV.
        window: Window,  # noqa: ARG002 - port signature; Alpaca serves OHLCV.
    ) -> dict[str, date]:
        """Return no earnings; Alpaca serves OHLCV only here."""
        return {}

    def _download(  # pragma: no cover - network I/O, paginated.
        self, tickers: tuple[str, ...], window: Window
    ) -> str:
        merged: dict[str, list[object]] = {}
        page_token: str | None = None
        while True:
            payload = self._download_page(tickers, window, page_token)
            page = json.loads(payload)
            for symbol, rows in (page.get("bars") or {}).items():
                merged.setdefault(symbol, []).extend(rows)
            page_token = page.get("next_page_token")
            if not page_token:
                break
        return json.dumps({"bars": merged})

    def _download_page(  # pragma: no cover - network I/O.
        self, tickers: tuple[str, ...], window: Window, page_token: str | None
    ) -> str:
        params = {
            "symbols": ",".join(tickers),
            "timeframe": "1Day",
            "start": window.start.isoformat(),
            "end": window.end.isoformat(),
            "feed": self._feed,
            "limit": "10000",
        }
        if page_token:
            params["page_token"] = page_token
        query = urllib.parse.urlencode(params)
        request = urllib.request.Request(  # noqa: S310 - hardcoded HTTPS Alpaca endpoint.
            f"{self._base_url}/v2/stocks/bars?{query}",
            headers={
                "APCA-API-KEY-ID": self._api_key,
                "APCA-API-SECRET-KEY": self._api_secret,
            },
        )
        with urllib.request.urlopen(request, timeout=self._timeout) as resp:  # noqa: S310
            return str(resp.read().decode("utf-8"))


def _parse_bars(raw_json: str, window: Window) -> tuple[OHLCVBar, ...]:
    """Parse Alpaca's multi-symbol bars payload into in-window OHLCV bars."""
    payload = json.loads(raw_json)
    if not isinstance(payload, dict):
        return ()
    bars_by_symbol = payload.get("bars")
    if not isinstance(bars_by_symbol, dict):
        return ()
    bars: list[OHLCVBar] = []
    for symbol, rows in bars_by_symbol.items():
        if not isinstance(rows, list):
            continue
        for item in rows:
            bar = _bar(str(symbol), item, window)
            if bar is not None:
                bars.append(bar)
    return tuple(bars)


def _bar(ticker: str, item: object, window: Window) -> OHLCVBar | None:
    if not isinstance(item, dict):
        return None
    try:
        # Alpaca bar timestamps are RFC-3339 (e.g. 2026-06-13T04:00:00Z); slice the
        # leading YYYY-MM-DD since fromisoformat rejects the trailing Z.
        bar_date = date.fromisoformat(str(item["t"])[:10])
        open_, high, low, close = (
            float(item["o"]),
            float(item["h"]),
            float(item["l"]),
            float(item["c"]),
        )
        volume = int(float(item["v"]))
    except (KeyError, TypeError, ValueError):
        return None
    if not window.start <= bar_date <= window.end:
        return None
    if min(open_, high, low, close) <= 0.0 or volume < 0:
        return None  # OHLCVBar requires positive prices; skip malformed rows.
    return OHLCVBar(
        ticker=ticker,
        bar_date=bar_date,
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=volume,
    )
