"""Finnhub fundamentals and news source over the provider DataSource boundary.

Agent: provider
Role: fetch per-ticker key metrics and recent headlines from Finnhub endpoints.
External I/O: optional HTTPS calls to finnhub.io.
"""

from __future__ import annotations

import urllib.parse
import urllib.request
from datetime import timedelta
from typing import TYPE_CHECKING

from agents.provider.fundamentals_parse import (
    _parse_metrics,
    _parse_news,
    _parse_next_earnings,
    _parse_sector,
)
from agents.provider.sources import RegimeInputs

if TYPE_CHECKING:
    from datetime import date

    from contracts.common import Window
    from contracts.provider import OHLCVBar


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
        earnings_lookahead_days: int = 30,
    ) -> None:
        """Create a Finnhub source from injected settings."""
        self._api_key = api_key
        self._base_url = base_url
        self._timeout = timeout
        self._news_lookback_days = news_lookback_days
        self._max_news_per_ticker = max_news_per_ticker
        self._earnings_lookahead_days = earnings_lookahead_days

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

    def fetch_sentiment(
        self,
        tickers: tuple[str, ...],  # noqa: ARG002 - Finnhub serves fundamentals/news.
    ) -> dict[str, float]:
        """Return no sentiment; Finnhub serves fundamentals/news only here."""
        return {}

    def fetch_sectors(self, tickers: tuple[str, ...]) -> dict[str, str]:
        """Fetch each ticker's sector/industry from Finnhub; skip when unknown."""
        out: dict[str, str] = {}
        for ticker in tickers:
            sector = _parse_sector(self._download_profile(ticker))
            if sector is not None:
                out[ticker] = sector
        return out

    def fetch_earnings(
        self, tickers: tuple[str, ...], window: Window
    ) -> dict[str, date]:
        """Fetch each ticker's next earnings date; skip when none upcoming."""
        from_date = window.end
        to_date = from_date + timedelta(days=self._earnings_lookahead_days)
        out: dict[str, date] = {}
        for ticker in tickers:
            next_date = _parse_next_earnings(
                self._download_earnings(ticker, from_date, to_date), from_date
            )
            if next_date is not None:
                out[ticker] = next_date
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

    def _download_profile(self, ticker: str) -> str:  # pragma: no cover
        query = urllib.parse.urlencode(
            {"symbol": ticker.upper(), "token": self._api_key}
        )
        with urllib.request.urlopen(  # noqa: S310 - hardcoded HTTPS Finnhub endpoint.
            f"{self._base_url}/stock/profile2?{query}", timeout=self._timeout
        ) as resp:
            return str(resp.read().decode("utf-8"))

    def _download_earnings(  # pragma: no cover
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
            f"{self._base_url}/calendar/earnings?{query}", timeout=self._timeout
        ) as resp:
            return str(resp.read().decode("utf-8"))
