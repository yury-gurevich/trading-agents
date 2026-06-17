"""Alpha Vantage news-sentiment source (provider-sentiment challenger, ADR-0002).

Agent: provider
Role: fetch a vendor per-ticker news-sentiment number from Alpha Vantage's
NEWS_SENTIMENT endpoint, aligned to the 0-1 lexicon scale (the advisory,
shadow challenger to the deterministic lexicon champion). Finnhub's equivalent
is dead (403 free); Alpha Vantage replaces it.
External I/O: optional HTTPS calls to www.alphavantage.co.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import TYPE_CHECKING

from agents.provider.sources import RegimeInputs

if TYPE_CHECKING:
    from datetime import date

    from contracts.common import Window
    from contracts.provider import OHLCVBar

_PATH = "/query"


class AlphaVantageSentimentSource:
    """Alpha Vantage NEWS_SENTIMENT source for per-ticker vendor sentiment."""

    def __init__(self, *, api_key: str, base_url: str, timeout: int) -> None:
        """Create an Alpha Vantage sentiment source from injected settings."""
        self._api_key = api_key
        self._base_url = base_url
        self._timeout = timeout

    def fetch_sentiment(self, tickers: tuple[str, ...]) -> dict[str, float]:
        """Return each requested ticker's mean vendor sentiment, aligned to 0-1."""
        if not tickers:
            return {}
        return _parse_sentiment(tickers, self._download(tickers))

    def fetch_ohlcv(
        self,
        tickers: tuple[str, ...],  # noqa: ARG002 - port signature; AV serves sentiment.
        window: Window,  # noqa: ARG002 - port signature; AV serves sentiment.
    ) -> tuple[OHLCVBar, ...]:
        """Return no bars; Alpha Vantage serves sentiment only here."""
        return ()

    def fetch_regime_inputs(self, as_of: date) -> RegimeInputs:
        """Return empty regime inputs; Alpha Vantage serves sentiment only here."""
        return RegimeInputs(as_of=as_of, vix=None)

    def fetch_fundamentals(
        self,
        tickers: tuple[str, ...],  # noqa: ARG002 - port signature; AV serves sentiment.
        window: Window,  # noqa: ARG002 - port signature; AV serves sentiment.
    ) -> dict[str, dict[str, float]]:
        """Return no fundamentals; Alpha Vantage serves sentiment only here."""
        return {}

    def fetch_news(
        self,
        tickers: tuple[str, ...],  # noqa: ARG002 - port signature; AV serves sentiment.
        window: Window,  # noqa: ARG002 - port signature; AV serves sentiment.
    ) -> dict[str, tuple[str, ...]]:
        """Return no news; Alpha Vantage serves sentiment only here."""
        return {}

    def fetch_sectors(
        self,
        tickers: tuple[str, ...],  # noqa: ARG002 - port signature; AV serves sentiment.
    ) -> dict[str, str]:
        """Return no sectors; Alpha Vantage serves sentiment only here."""
        return {}

    def _download(self, tickers: tuple[str, ...]) -> str:  # pragma: no cover
        query = urllib.parse.urlencode(
            {
                "function": "NEWS_SENTIMENT",
                "tickers": ",".join(ticker.upper() for ticker in tickers),
                "limit": 200,
                "apikey": self._api_key,
            }
        )
        with urllib.request.urlopen(  # noqa: S310 - hardcoded HTTPS Alpha Vantage endpoint
            f"{self._base_url}{_PATH}?{query}", timeout=self._timeout
        ) as resp:
            return str(resp.read().decode("utf-8"))


def _parse_sentiment(tickers: tuple[str, ...], raw_json: str) -> dict[str, float]:
    """Average each requested ticker's per-article sentiment, aligned to 0-1."""
    payload = json.loads(raw_json)
    feed = payload.get("feed") if isinstance(payload, dict) else None
    if not isinstance(feed, list):
        return {}
    wanted = {ticker.upper() for ticker in tickers}
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}
    for article in feed:
        if not isinstance(article, dict):
            continue
        for entry in article.get("ticker_sentiment", []):
            _accumulate(entry, wanted, totals, counts)
    return {sym: _align(totals[sym] / counts[sym]) for sym in totals}


def _accumulate(
    entry: object,
    wanted: set[str],
    totals: dict[str, float],
    counts: dict[str, int],
) -> None:
    if not isinstance(entry, dict):
        return
    sym = str(entry.get("ticker", "")).upper()
    if sym not in wanted:
        return
    try:
        score = float(entry["ticker_sentiment_score"])
    except (KeyError, TypeError, ValueError):
        return
    totals[sym] = totals.get(sym, 0.0) + score
    counts[sym] = counts.get(sym, 0) + 1


def _align(raw: float) -> float:
    """Map Alpha Vantage's [-1, 1] sentiment onto the 0-1 lexicon scale."""
    return max(0.0, min(1.0, (raw + 1.0) / 2.0))
