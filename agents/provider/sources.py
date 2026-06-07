"""Provider data-source ports and concrete source adapters.

Agent: provider
Role: isolate market-data fetches behind a deterministic DataSource boundary.
External I/O: optional HTTPS calls to Stooq.
"""

from __future__ import annotations

import csv
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Protocol

from contracts.provider import OHLCVBar

if TYPE_CHECKING:
    from collections.abc import Mapping

    from contracts.common import Window


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


class FakeDataSource:
    """Deterministic source used by the unit gate."""

    def __init__(
        self,
        *,
        bars: tuple[OHLCVBar, ...] = (),
        vix: float | None = None,
        fail_ohlcv: bool = False,
        fail_regime: bool = False,
    ) -> None:
        """Create a deterministic fixture source."""
        self._bars = bars
        self._vix = vix
        self._fail_ohlcv = fail_ohlcv
        self._fail_regime = fail_regime

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
    return all(row.get(name) for name in ("Date", "Open", "High", "Low", "Close"))
