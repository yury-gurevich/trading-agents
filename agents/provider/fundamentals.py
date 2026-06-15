"""Finnhub fundamentals and news source over the provider DataSource boundary.

Agent: provider
Role: fetch per-ticker key metrics and recent headlines from Finnhub endpoints.
External I/O: optional HTTPS calls to finnhub.io.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import timedelta
from typing import TYPE_CHECKING

from agents.provider.sources import RegimeInputs

if TYPE_CHECKING:
    from datetime import date

    from contracts.common import Window
    from contracts.provider import OHLCVBar

# Fixed Finnhub /stock/metric field names (the union of primary + fallback keys the
# analyst reads). These are API field identifiers, not tunable policy.
_FUNDAMENTAL_KEYS: tuple[str, ...] = (
    "peBasicExclExtraTTM",
    "peTTM",
    "roeTTM",
    "netProfitMarginTTM",
    "currentRatioQuarterly",
    "pbQuarterly",
    "pbAnnual",
    "totalDebt/totalEquityQuarterly",
    "totalDebt/totalEquityAnnual",
    "epsGrowthTTMYoy",
    "revenueGrowthTTMYoy",
)


class FinnhubDataSource:
    """Finnhub source for fundamentals and recent company news."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        timeout: int,
        news_lookback_days: int = 7,
        max_news_per_ticker: int = 20,
    ) -> None:
        """Create a Finnhub source from injected settings."""
        self._api_key = api_key
        self._base_url = base_url
        self._timeout = timeout
        self._news_lookback_days = news_lookback_days
        self._max_news_per_ticker = max_news_per_ticker

    def fetch_ohlcv(
        self,
        tickers: tuple[str, ...],  # noqa: ARG002 - port signature; no OHLCV here.
        window: Window,  # noqa: ARG002 - port signature; no OHLCV here.
    ) -> tuple[OHLCVBar, ...]:
        """Return no bars; Finnhub daily candles are premium-only here."""
        return ()

    def fetch_regime_inputs(self, as_of: date) -> RegimeInputs:
        """Return empty regime inputs; this source serves fundamentals only."""
        return RegimeInputs(as_of=as_of, vix=None)

    def fetch_fundamentals(
        self,
        tickers: tuple[str, ...],
        window: Window,  # noqa: ARG002 - port signature; metric endpoint is point-in-time.
    ) -> dict[str, dict[str, float]]:
        """Fetch key metrics per ticker; skip tickers with no usable metric."""
        out: dict[str, dict[str, float]] = {}
        for ticker in tickers:
            metrics = _parse_metrics(self._download(ticker))
            if metrics:
                out[ticker] = metrics
        return out

    def fetch_news(
        self,
        tickers: tuple[str, ...],
        window: Window,
    ) -> dict[str, tuple[str, ...]]:
        """Fetch recent headlines per ticker; skip tickers with no usable headline."""
        news_to = window.end
        news_from = news_to - timedelta(days=self._news_lookback_days)
        out: dict[str, tuple[str, ...]] = {}
        for ticker in tickers:
            headlines = _parse_news(
                self._download_news(ticker, news_from, news_to),
                self._max_news_per_ticker,
            )
            if headlines:
                out[ticker] = headlines
        return out

    def _download(self, ticker: str) -> str:  # pragma: no cover
        query = urllib.parse.urlencode(
            {"symbol": ticker.upper(), "metric": "all", "token": self._api_key}
        )
        with urllib.request.urlopen(  # noqa: S310 - hardcoded HTTPS Finnhub endpoint.
            f"{self._base_url}/stock/metric?{query}", timeout=self._timeout
        ) as resp:
            return str(resp.read().decode("utf-8"))

    def _download_news(  # pragma: no cover
        self, ticker: str, from_date: date, to_date: date
    ) -> str:
        query = urllib.parse.urlencode(
            {
                "symbol": ticker.upper(),
                "from": from_date.isoformat(),
                "to": to_date.isoformat(),
                "token": self._api_key,
            }
        )
        with urllib.request.urlopen(  # noqa: S310 - hardcoded HTTPS Finnhub endpoint.
            f"{self._base_url}/company-news?{query}", timeout=self._timeout
        ) as resp:
            return str(resp.read().decode("utf-8"))


def _parse_metrics(raw_json: str) -> dict[str, float]:
    """Extract float-coercible target keys from a Finnhub metric response."""
    payload = json.loads(raw_json)
    metric = payload.get("metric") if isinstance(payload, dict) else None
    if not isinstance(metric, dict):
        return {}
    out: dict[str, float] = {}
    for key in _FUNDAMENTAL_KEYS:
        value = metric.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        out[key] = float(value)
    return out


def _parse_news(raw_json: str, cap: int) -> tuple[str, ...]:
    """Extract headline strings from a Finnhub /company-news response array.

    Never raises; returns an empty tuple for any malformed or empty payload.
    Newest-first order is preserved (Finnhub returns articles newest-first).
    """
    try:
        payload = json.loads(raw_json)
    except (json.JSONDecodeError, ValueError):
        return ()
    if not isinstance(payload, list):
        return ()
    headlines: list[str] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        headline = item.get("headline")
        if not isinstance(headline, str) or not headline:
            continue
        headlines.append(str(headline))
        if len(headlines) >= cap:
            break
    return tuple(headlines)
