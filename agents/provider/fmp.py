"""FinancialModelingPrep EOD source over the provider DataSource boundary.

Agent: provider
Role: fetch daily OHLCV bars from FMP's stable historical-price-eod endpoint
(the live OHLCV feed after Stooq became anti-bot-blocked — DRIFT-009).
External I/O: optional HTTPS calls to financialmodelingprep.com.
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

_EOD_PATH = "/stable/historical-price-eod/full"


class FMPDataSource:
    """FinancialModelingPrep stable-EOD source for daily OHLCV bars."""

    def __init__(self, *, api_key: str, base_url: str, timeout: int) -> None:
        """Create an FMP OHLCV source from injected settings."""
        self._api_key = api_key
        self._base_url = base_url
        self._timeout = timeout

    def fetch_ohlcv(
        self, tickers: tuple[str, ...], window: Window
    ) -> tuple[OHLCVBar, ...]:
        """Fetch daily OHLCV bars from FMP for each ticker, within the window."""
        bars: list[OHLCVBar] = []
        for ticker in tickers:
            bars.extend(_parse_eod(ticker, self._download(ticker, window), window))
        return tuple(bars)

    def fetch_regime_inputs(self, as_of: date) -> RegimeInputs:
        """Return empty regime inputs; FMP serves OHLCV only here."""
        return RegimeInputs(as_of=as_of, vix=None)

    def fetch_fundamentals(
        self,
        tickers: tuple[str, ...],  # noqa: ARG002 - port signature; FMP serves OHLCV.
        window: Window,  # noqa: ARG002 - port signature; FMP serves OHLCV.
    ) -> dict[str, dict[str, float]]:
        """Return no fundamentals; FMP serves OHLCV only here."""
        return {}

    def fetch_news(
        self,
        tickers: tuple[str, ...],  # noqa: ARG002 - port signature; FMP serves OHLCV.
        window: Window,  # noqa: ARG002 - port signature; FMP serves OHLCV.
    ) -> dict[str, tuple[str, ...]]:
        """Return no news; FMP serves OHLCV only here."""
        return {}

    def fetch_sentiment(
        self,
        tickers: tuple[str, ...],  # noqa: ARG002 - port signature; FMP serves OHLCV.
    ) -> dict[str, float]:
        """Return no sentiment; FMP serves OHLCV only here."""
        return {}

    def fetch_sectors(
        self,
        tickers: tuple[str, ...],  # noqa: ARG002 - port signature; FMP serves OHLCV.
    ) -> dict[str, str]:
        """Return no sectors; FMP serves OHLCV only here."""
        return {}

    def _download(self, ticker: str, window: Window) -> str:  # pragma: no cover
        query = urllib.parse.urlencode(
            {
                "symbol": ticker.upper(),
                "from": window.start.isoformat(),
                "to": window.end.isoformat(),
                "apikey": self._api_key,
            }
        )
        with urllib.request.urlopen(  # noqa: S310 - hardcoded HTTPS FMP endpoint.
            f"{self._base_url}{_EOD_PATH}?{query}", timeout=self._timeout
        ) as resp:
            return str(resp.read().decode("utf-8"))


def _parse_eod(ticker: str, raw_json: str, window: Window) -> tuple[OHLCVBar, ...]:
    """Parse an FMP EOD JSON array into in-window OHLCV bars; skip malformed rows."""
    payload = json.loads(raw_json)
    if not isinstance(payload, list):
        return ()
    bars: list[OHLCVBar] = []
    for item in payload:
        bar = _bar(ticker, item, window)
        if bar is not None:
            bars.append(bar)
    return tuple(bars)


def _bar(ticker: str, item: object, window: Window) -> OHLCVBar | None:
    if not isinstance(item, dict):
        return None
    try:
        bar_date = date.fromisoformat(str(item["date"]))
        open_, high, low, close = (
            float(item["open"]),
            float(item["high"]),
            float(item["low"]),
            float(item["close"]),
        )
        volume = int(float(item["volume"]))
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
