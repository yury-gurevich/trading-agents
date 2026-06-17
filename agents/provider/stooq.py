"""Keyless Stooq CSV source (retired default; anti-bot-blocked — DRIFT-009).

Agent: provider
Role: legacy daily-OHLCV source, kept for the network-gated integration test only;
Tiingo is the runtime default (ADR-0006).
External I/O: optional HTTPS calls to stooq.com.
"""

from __future__ import annotations

import csv
import urllib.parse
import urllib.request
from datetime import date
from typing import TYPE_CHECKING

from agents.provider.sources import RegimeInputs
from contracts.provider import OHLCVBar

if TYPE_CHECKING:
    from collections.abc import Mapping

    from contracts.common import Window


class StooqDataSource:
    """Keyless Stooq CSV source for daily OHLCV bars."""

    _base_url = "https://stooq.com/q/d/l/"

    def fetch_ohlcv(
        self, tickers: tuple[str, ...], window: Window
    ) -> tuple[OHLCVBar, ...]:
        """Fetch daily OHLCV bars from Stooq's CSV endpoint."""
        bars: list[OHLCVBar] = []
        for ticker in tickers:
            bars.extend(_parse_stooq_rows(ticker, self._download(ticker, window)))
        return tuple(bars)

    def fetch_regime_inputs(self, as_of: date) -> RegimeInputs:
        """Return empty regime inputs; keyed macro/VIX sources land later."""
        return RegimeInputs(as_of=as_of, vix=None)

    def fetch_fundamentals(
        self,
        tickers: tuple[str, ...],  # noqa: ARG002 - port signature; Stooq has none.
        window: Window,  # noqa: ARG002 - port signature; Stooq has none.
    ) -> dict[str, dict[str, float]]:
        """Return no fundamentals; Stooq serves OHLCV only."""
        return {}

    def fetch_news(
        self,
        tickers: tuple[str, ...],  # noqa: ARG002 - port signature; Stooq has none.
        window: Window,  # noqa: ARG002 - port signature; Stooq has none.
    ) -> dict[str, tuple[str, ...]]:
        """Return no news; Stooq serves OHLCV only."""
        return {}

    def fetch_sentiment(
        self,
        tickers: tuple[str, ...],  # noqa: ARG002 - port signature; Stooq has none.
    ) -> dict[str, float]:
        """Return no sentiment; Stooq serves OHLCV only."""
        return {}

    def fetch_sectors(
        self,
        tickers: tuple[str, ...],  # noqa: ARG002 - port signature; Stooq has none.
    ) -> dict[str, str]:
        """Return no sectors; Stooq serves OHLCV only."""
        return {}

    def fetch_earnings(
        self,
        tickers: tuple[str, ...],  # noqa: ARG002 - port signature; Stooq has none.
        window: Window,  # noqa: ARG002 - port signature; Stooq has none.
    ) -> dict[str, date]:
        """Return no earnings; Stooq serves OHLCV only."""
        return {}

    def _download(self, ticker: str, window: Window) -> str:  # pragma: no cover
        query = urllib.parse.urlencode(
            {
                "s": f"{ticker.lower()}.us",
                "d1": window.start.strftime("%Y%m%d"),
                "d2": window.end.strftime("%Y%m%d"),
                "i": "d",
            }
        )
        with urllib.request.urlopen(  # noqa: S310 - hardcoded HTTPS Stooq endpoint.
            f"{self._base_url}?{query}", timeout=10
        ) as resp:
            return str(resp.read().decode("utf-8"))


def _parse_stooq_rows(ticker: str, raw_csv: str) -> tuple[OHLCVBar, ...]:
    rows: list[OHLCVBar] = []
    for row in csv.DictReader(raw_csv.splitlines()):
        if not _has_ohlcv(row):
            continue
        rows.append(
            OHLCVBar(
                ticker=ticker,
                bar_date=date.fromisoformat(str(row["Date"])),
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=int(float(row["Volume"])),
            )
        )
    return tuple(rows)


def _has_ohlcv(row: Mapping[str, str]) -> bool:
    return all(row.get(n) for n in ("Date", "Open", "High", "Low", "Close", "Volume"))
