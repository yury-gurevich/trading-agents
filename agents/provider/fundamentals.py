"""Finnhub fundamentals and news source over the provider DataSource boundary.

Agent: provider
Role: fetch per-ticker key metrics and recent headlines from Finnhub endpoints.
External I/O: optional HTTPS calls to finnhub.io.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from agents.provider.finnhub_http import FinnhubHttpClient
from agents.provider.finnhub_resilience import FeedFailureCollector
from agents.provider.fundamentals_parse import (
    _parse_metrics,
    _parse_news,
    _parse_next_earnings,
    _parse_sector,
)
from agents.provider.sources import RegimeInputs

if TYPE_CHECKING:
    from collections.abc import Callable
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
        request_budget_per_minute: int = 55,
        degraded_note_ticker_cap: int = 5,
        clock: Callable[[], float] | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        """Create a Finnhub source from injected settings."""
        self._client = FinnhubHttpClient(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            request_budget_per_minute=request_budget_per_minute,
            clock=clock,
            sleep=sleep,
        )
        self._news_lookback_days = news_lookback_days
        self._max_news_per_ticker = max_news_per_ticker
        self._earnings_lookahead_days = earnings_lookahead_days
        self._degraded_note_ticker_cap = degraded_note_ticker_cap
        self._degraded_notes: list[str] = []

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
        failures = self._failures("fundamentals")
        for ticker in tickers:
            metrics = failures.capture(
                ticker, lambda t: _parse_metrics(self._download(t))
            )
            if metrics:
                out[ticker] = metrics
        self._record_failures(failures)
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
        failures = self._failures("news")
        for ticker in tickers:
            headlines = failures.capture(
                ticker,
                lambda t: _parse_news(
                    self._download_news(t, news_from, news_to),
                    self._max_news_per_ticker,
                ),
            )
            if headlines:
                out[ticker] = headlines
        self._record_failures(failures)
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
        failures = self._failures("sectors")
        for ticker in tickers:
            sector = failures.capture(
                ticker, lambda t: _parse_sector(self._download_profile(t))
            )
            if sector is not None:
                out[ticker] = sector
        self._record_failures(failures)
        return out

    def fetch_earnings(
        self, tickers: tuple[str, ...], window: Window
    ) -> dict[str, date]:
        """Fetch each ticker's next earnings date; skip when none upcoming."""
        from_date = window.end
        to_date = from_date + timedelta(days=self._earnings_lookahead_days)
        out: dict[str, date] = {}
        failures = self._failures("earnings")
        for ticker in tickers:
            next_date = failures.capture(
                ticker,
                lambda t: _parse_next_earnings(
                    self._download_earnings(t, from_date, to_date), from_date
                ),
            )
            if next_date is not None:
                out[ticker] = next_date
        self._record_failures(failures)
        return out

    def consume_degraded_feed_notes(self) -> tuple[str, ...]:
        """Drain per-ticker feed notes produced by the last source call."""
        notes = tuple(self._degraded_notes)
        self._degraded_notes.clear()
        return notes

    def _record_failures(self, failures: FeedFailureCollector) -> None:
        note = failures.note()
        if note is not None:
            self._degraded_notes.append(note)

    def _failures(self, feed: str) -> FeedFailureCollector:
        return FeedFailureCollector(feed, ticker_cap=self._degraded_note_ticker_cap)

    def _download(self, ticker: str) -> str:  # pragma: no cover
        return self._client.metric(ticker)

    def _download_news(  # pragma: no cover
        self, ticker: str, from_date: date, to_date: date
    ) -> str:
        return self._client.news(ticker, from_date, to_date)

    def _download_profile(self, ticker: str) -> str:  # pragma: no cover
        return self._client.profile(ticker)

    def _download_earnings(  # pragma: no cover
        self, ticker: str, from_date: date, to_date: date
    ) -> str:
        return self._client.earnings(ticker, from_date, to_date)
