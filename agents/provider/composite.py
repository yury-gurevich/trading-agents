"""Composite DataSource routing OHLCV/regime, fundamentals/news, and sentiment.

Agent: provider
Role: combine a price/regime source (Tiingo), a fundamentals/news source (Finnhub),
and a sentiment source (Alpha Vantage).
External I/O: none directly (delegates to the wrapped sources).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date

    from agents.provider.settings import ProviderSettings
    from agents.provider.sources import DataSource, RegimeInputs
    from contracts.common import Window
    from contracts.provider import OHLCVBar


class CompositeDataSource:
    """Route price/regime to one source and fundamentals to another."""

    def __init__(
        self,
        price_source: DataSource,
        fundamentals_source: DataSource,
        sentiment_source: DataSource,
    ) -> None:
        """Wrap a price/regime, a fundamentals/news, and a sentiment source."""
        self._price_source = price_source
        self._fundamentals_source = fundamentals_source
        self._sentiment_source = sentiment_source

    def fetch_ohlcv(
        self, tickers: tuple[str, ...], window: Window
    ) -> tuple[OHLCVBar, ...]:
        """Delegate OHLCV fetches to the price source."""
        return self._price_source.fetch_ohlcv(tickers, window)

    def fetch_regime_inputs(self, as_of: date) -> RegimeInputs:
        """Delegate regime-input fetches to the price source."""
        return self._price_source.fetch_regime_inputs(as_of)

    def fetch_fundamentals(
        self, tickers: tuple[str, ...], window: Window
    ) -> dict[str, dict[str, float]]:
        """Delegate fundamentals fetches to the fundamentals source."""
        return self._fundamentals_source.fetch_fundamentals(tickers, window)

    def fetch_news(
        self, tickers: tuple[str, ...], window: Window
    ) -> dict[str, tuple[str, ...]]:
        """Delegate news fetches to the fundamentals (Finnhub) source."""
        return self._fundamentals_source.fetch_news(tickers, window)

    def fetch_sentiment(self, tickers: tuple[str, ...]) -> dict[str, float]:
        """Delegate vendor-sentiment fetches to the sentiment (Alpha Vantage) source."""
        return self._sentiment_source.fetch_sentiment(tickers)

    def fetch_sectors(self, tickers: tuple[str, ...]) -> dict[str, str]:
        """Delegate sector fetches to the fundamentals (Finnhub) source."""
        return self._fundamentals_source.fetch_sectors(tickers)

    def fetch_earnings(
        self, tickers: tuple[str, ...], window: Window
    ) -> dict[str, date]:
        """Delegate earnings fetches to the fundamentals (Finnhub) source."""
        return self._fundamentals_source.fetch_earnings(tickers, window)


def market_source_from_settings(settings: ProviderSettings) -> CompositeDataSource:
    """Compose live feeds: Tiingo OHLCV + Finnhub fundamentals/news + AV sentiment."""
    from agents.provider.av_sentiment import AlphaVantageSentimentSource
    from agents.provider.fundamentals import FinnhubDataSource
    from agents.provider.tiingo import TiingoDataSource

    return CompositeDataSource(
        price_source=TiingoDataSource(
            api_key=settings.tiingo_api_key,
            base_url=settings.tiingo_base_url,
            timeout=settings.tiingo_timeout,
        ),
        fundamentals_source=FinnhubDataSource(
            api_key=settings.finnhub_api_key,
            base_url=settings.finnhub_base_url,
            timeout=settings.finnhub_timeout,
            earnings_lookahead_days=settings.finnhub_earnings_lookahead_days,
        ),
        sentiment_source=AlphaVantageSentimentSource(
            api_key=settings.alphavantage_api_key,
            base_url=settings.alphavantage_base_url,
            timeout=settings.alphavantage_timeout,
        ),
    )
