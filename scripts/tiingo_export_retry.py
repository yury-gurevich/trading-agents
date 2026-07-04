"""Bounded retry helper for Tiingo exporter calls.

Agent: tooling
Role: retry transient Tiingo fetch failures without bypassing hourly pacing.
External I/O: calls an injected source and sleeps between retry attempts.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Protocol
from urllib.error import HTTPError, URLError

if TYPE_CHECKING:
    from contracts.common import Window

DEFAULT_BACKOFF_SECONDS = 30.0
TRANSIENT_HTTP_CODES = {500, 502, 503, 504}


class OhlcvSource(Protocol):
    """Minimal source protocol needed by the exporter retry helper."""

    def fetch_ohlcv(
        self, tickers: tuple[str, ...], window: Window
    ) -> tuple[object, ...]:
        """Fetch OHLCV bars for one or more tickers."""


def fetch_with_backoff(
    source: OhlcvSource,
    ticker: str,
    window: Window,
    *,
    max_retries: int,
    backoff_seconds: float,
) -> tuple[object, ...]:
    """Fetch one ticker with bounded transient retry; let 429 bubble to caller."""
    attempts = 0
    while True:
        try:
            return source.fetch_ohlcv((ticker,), window)
        except HTTPError as exc:
            if exc.code == 429 or exc.code not in TRANSIENT_HTTP_CODES:
                raise
            if attempts >= max_retries:
                raise
            attempts += 1
            time.sleep(backoff_seconds * attempts)
        except (TimeoutError, URLError):
            if attempts >= max_retries:
                raise
            attempts += 1
            time.sleep(backoff_seconds * attempts)
