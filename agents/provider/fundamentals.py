"""Finnhub fundamentals source over the provider DataSource boundary.

Agent: provider
Role: fetch per-ticker key metrics from Finnhub's /stock/metric endpoint (no OHLCV).
External I/O: optional HTTPS calls to finnhub.io.
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
    """Fundamentals-only source backed by Finnhub's /stock/metric endpoint."""

    def __init__(self, *, api_key: str, base_url: str, timeout: int) -> None:
        """Create a Finnhub fundamentals source from injected settings."""
        self._api_key = api_key
        self._base_url = base_url
        self._timeout = timeout

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

    def _download(self, ticker: str) -> str:  # pragma: no cover
        query = urllib.parse.urlencode(
            {"symbol": ticker.upper(), "metric": "all", "token": self._api_key}
        )
        with urllib.request.urlopen(  # noqa: S310 - hardcoded HTTPS Finnhub endpoint.
            f"{self._base_url}/stock/metric?{query}", timeout=self._timeout
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
