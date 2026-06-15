"""Composite DataSource that routes OHLCV/regime and fundamentals to different feeds.

Agent: provider
Role: combine a price/regime source (Stooq) with a fundamentals source (Finnhub).
External I/O: none directly (delegates to the wrapped sources).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date

    from agents.provider.sources import DataSource, RegimeInputs
    from contracts.common import Window
    from contracts.provider import OHLCVBar


class CompositeDataSource:
    """Route price/regime to one source and fundamentals to another."""

    def __init__(
        self, price_source: DataSource, fundamentals_source: DataSource
    ) -> None:
        """Wrap a price/regime source and a fundamentals source."""
        self._price_source = price_source
        self._fundamentals_source = fundamentals_source

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
