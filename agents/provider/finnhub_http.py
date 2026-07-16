"""Finnhub HTTPS client with per-request pacing.

Agent: provider
Role: construct declared Finnhub endpoint URLs and pace every HTTP request.
External I/O: optional HTTPS calls to finnhub.io.
"""

from __future__ import annotations

import urllib.parse
import urllib.request
from typing import TYPE_CHECKING

from agents.provider.finnhub_resilience import RequestRateBudget

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import date


class FinnhubHttpClient:
    """Small paced client for the Finnhub endpoints used by the provider."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        timeout: int,
        request_budget_per_minute: int,
        clock: Callable[[], float] | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        """Create a client with the configured timeout and request budget."""
        self._api_key = api_key
        self._base_url = base_url
        self._timeout = timeout
        self._rate_budget = RequestRateBudget(
            request_budget_per_minute, clock=clock, sleep=sleep
        )

    def metric(self, ticker: str) -> str:  # pragma: no cover
        """Download Finnhub /stock/metric for one ticker."""
        return self._get(
            "/stock/metric",
            {"symbol": ticker.upper(), "metric": "all", "token": self._api_key},
        )

    def news(
        self, ticker: str, from_date: date, to_date: date
    ) -> str:  # pragma: no cover
        """Download Finnhub /company-news for one ticker."""
        return self._get(
            "/company-news",
            {
                "symbol": ticker.upper(),
                "from": from_date.isoformat(),
                "to": to_date.isoformat(),
                "token": self._api_key,
            },
        )

    def profile(self, ticker: str) -> str:  # pragma: no cover
        """Download Finnhub /stock/profile2 for one ticker."""
        return self._get(
            "/stock/profile2", {"symbol": ticker.upper(), "token": self._api_key}
        )

    def earnings(
        self, ticker: str, from_date: date, to_date: date
    ) -> str:  # pragma: no cover
        """Download Finnhub /calendar/earnings for one ticker."""
        return self._get(
            "/calendar/earnings",
            {
                "symbol": ticker.upper(),
                "from": from_date.isoformat(),
                "to": to_date.isoformat(),
                "token": self._api_key,
            },
        )

    def _get(self, path: str, params: dict[str, str]) -> str:  # pragma: no cover
        query = urllib.parse.urlencode(params)
        self._rate_budget.wait()
        with urllib.request.urlopen(  # noqa: S310 - declared HTTPS Finnhub endpoint.
            f"{self._base_url}{path}?{query}", timeout=self._timeout
        ) as resp:
            return str(resp.read().decode("utf-8"))
