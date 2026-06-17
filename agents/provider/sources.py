"""Provider data-source ports and concrete source adapters.

Agent: provider
Role: isolate market-data fetches behind a deterministic DataSource boundary.
External I/O: none here (concrete clients live in their own modules).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from datetime import date

    from contracts.common import Window
    from contracts.provider import OHLCVBar


@dataclass(frozen=True)
class RegimeInputs:
    """Raw market-regime inputs fetched by the provider boundary."""

    as_of: date
    vix: float | None = None


class DataSource(Protocol):
    """Boundary for all provider-owned external data clients."""

    def fetch_ohlcv(
        self, tickers: tuple[str, ...], window: Window
    ) -> tuple[OHLCVBar, ...]:
        """Fetch daily OHLCV bars for tickers over a date window."""
        ...  # pragma: no cover - protocol declaration only.

    def fetch_regime_inputs(self, as_of: date) -> RegimeInputs:
        """Fetch raw inputs used to classify the market regime."""
        ...  # pragma: no cover - protocol declaration only.

    def fetch_fundamentals(
        self, tickers: tuple[str, ...], window: Window
    ) -> dict[str, dict[str, float]]:
        """Fetch per-ticker fundamental metrics; empty dict per ticker on no data."""
        ...  # pragma: no cover - protocol declaration only.

    def fetch_news(
        self, tickers: tuple[str, ...], window: Window
    ) -> dict[str, tuple[str, ...]]:
        """Fetch per-ticker recent headlines; skip tickers with no usable headline."""
        ...  # pragma: no cover - protocol declaration only.

    def fetch_sentiment(self, tickers: tuple[str, ...]) -> dict[str, float]:
        """Fetch per-ticker vendor sentiment (0-1); empty when none available."""
        ...  # pragma: no cover - protocol declaration only.

    def fetch_sectors(self, tickers: tuple[str, ...]) -> dict[str, str]:
        """Fetch per-ticker sector/industry label; empty when none available."""
        ...  # pragma: no cover - protocol declaration only.

    def fetch_earnings(
        self, tickers: tuple[str, ...], window: Window
    ) -> dict[str, date]:
        """Fetch per-ticker next earnings date; skip tickers with none upcoming."""
        ...  # pragma: no cover - protocol declaration only.


class FakeDataSource:
    """Deterministic source used by the unit gate."""

    def __init__(
        self,
        *,
        bars: tuple[OHLCVBar, ...] = (),
        vix: float | None = None,
        fundamentals: dict[str, dict[str, float]] | None = None,
        news: dict[str, tuple[str, ...]] | None = None,
        sentiment: dict[str, float] | None = None,
        sectors: dict[str, str] | None = None,
        earnings: dict[str, date] | None = None,
        fail_ohlcv: bool = False,
        fail_regime: bool = False,
        fail_fundamentals: bool = False,
        fail_news: bool = False,
        fail_sentiment: bool = False,
        fail_sectors: bool = False,
        fail_earnings: bool = False,
    ) -> None:
        """Create a deterministic fixture source."""
        self._bars = bars
        self._vix = vix
        self._fundamentals = fundamentals or {}
        self._news = news or {}
        self._sentiment = sentiment or {}
        self._sectors = sectors or {}
        self._earnings = earnings or {}
        self._fail_ohlcv = fail_ohlcv
        self._fail_regime = fail_regime
        self._fail_fundamentals = fail_fundamentals
        self._fail_news = fail_news
        self._fail_sentiment = fail_sentiment
        self._fail_sectors = fail_sectors
        self._fail_earnings = fail_earnings

    def fetch_ohlcv(
        self, tickers: tuple[str, ...], window: Window
    ) -> tuple[OHLCVBar, ...]:
        """Return matching fixture bars or raise the requested fixture failure."""
        if self._fail_ohlcv:
            raise RuntimeError("source unavailable")
        ticker_set = set(tickers)
        return tuple(
            bar
            for bar in self._bars
            if bar.ticker in ticker_set and window.start <= bar.bar_date <= window.end
        )

    def fetch_regime_inputs(self, as_of: date) -> RegimeInputs:
        """Return fixture regime inputs or raise the requested fixture failure."""
        if self._fail_regime:
            raise RuntimeError("regime source unavailable")
        return RegimeInputs(as_of=as_of, vix=self._vix)

    def fetch_fundamentals(
        self,
        tickers: tuple[str, ...],
        window: Window,  # noqa: ARG002 - port signature; metrics are point-in-time.
    ) -> dict[str, dict[str, float]]:
        """Return the fixture metric subset for requested tickers, or raise."""
        if self._fail_fundamentals:
            raise RuntimeError("fundamentals source unavailable")
        return {
            ticker: self._fundamentals[ticker]
            for ticker in tickers
            if ticker in self._fundamentals
        }

    def fetch_news(
        self,
        tickers: tuple[str, ...],
        window: Window,  # noqa: ARG002 - port signature; fixture is window-independent.
    ) -> dict[str, tuple[str, ...]]:
        """Return the fixture headline subset for requested tickers, or raise."""
        if self._fail_news:
            raise RuntimeError("news source unavailable")
        return {
            ticker: self._news[ticker] for ticker in tickers if ticker in self._news
        }

    def fetch_sentiment(self, tickers: tuple[str, ...]) -> dict[str, float]:
        """Return the fixture sentiment subset for requested tickers, or raise."""
        if self._fail_sentiment:
            raise RuntimeError("sentiment source unavailable")
        return {
            ticker: self._sentiment[ticker]
            for ticker in tickers
            if ticker in self._sentiment
        }

    def fetch_sectors(self, tickers: tuple[str, ...]) -> dict[str, str]:
        """Return the fixture sector subset for requested tickers, or raise."""
        if self._fail_sectors:
            raise RuntimeError("sectors source unavailable")
        return {
            ticker: self._sectors[ticker]
            for ticker in tickers
            if ticker in self._sectors
        }

    def fetch_earnings(
        self,
        tickers: tuple[str, ...],
        window: Window,  # noqa: ARG002 - port signature; fixture is window-independent.
    ) -> dict[str, date]:
        """Return the fixture earnings subset for requested tickers, or raise."""
        if self._fail_earnings:
            raise RuntimeError("earnings source unavailable")
        return {
            ticker: self._earnings[ticker]
            for ticker in tickers
            if ticker in self._earnings
        }
