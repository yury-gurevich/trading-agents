"""Fixtures for the run as-of tests (S249, DL-256).

Agent: provider
Role: a RunRequest written the way the dispatcher writes it, and data sources
      that record the window, regime date and news/earnings anchors they are asked for.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from agents.provider import ProviderAgent
from agents.provider.fundamentals import FinnhubDataSource
from agents.provider.sources import FakeDataSource, RegimeInputs
from contracts.provider import (
    MARKET_DATA_LABEL,
    REGIME_CONTEXT_LABEL,
    RUN_REQUEST_LABEL,
    RUN_REQUEST_LOOKBACK_DAYS_PROP,
    RUN_REQUEST_REQUESTED_AT_PROP,
    RUN_REQUEST_REQUIRED_HISTORY_BARS_PROP,
)
from kernel import InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from datetime import date

    from agents.provider.settings import ProviderSettings
    from contracts.common import Window
    from contracts.provider import OHLCVBar
    from kernel import Node


class RecordingSource(FakeDataSource):
    """A fixture source that remembers each OHLCV window and regime date asked of it."""

    def __init__(self) -> None:
        """Create an empty recorder over a source that serves no bars."""
        super().__init__()
        self.ohlcv_windows: list[Window] = []
        self.regime_dates: list[date] = []

    def fetch_ohlcv(
        self, tickers: tuple[str, ...], window: Window
    ) -> tuple[OHLCVBar, ...]:
        """Record the window, then serve the fixture's (empty) bars."""
        self.ohlcv_windows.append(window)
        return super().fetch_ohlcv(tickers, window)

    def fetch_regime_inputs(self, as_of: date) -> RegimeInputs:
        """Record the regime date, then serve the fixture's inputs."""
        self.regime_dates.append(as_of)
        return super().fetch_regime_inputs(as_of)

    @property
    def calls(self) -> int:
        """Every OHLCV and regime fetch made so far."""
        return len(self.ohlcv_windows) + len(self.regime_dates)


class RecordingFinnhub(FinnhubDataSource):
    """A Finnhub source with no network: the news and earnings dates asked are kept."""

    def __init__(self, news_lookback_days: int) -> None:
        """Create the source with pacing off and an empty record."""
        super().__init__(
            api_key="",
            base_url="https://finnhub.invalid",
            timeout=1,
            news_lookback_days=news_lookback_days,
            request_budget_per_minute=0,
        )
        self.asked: dict[str, tuple[date, date]] = {}

    @override
    def _download(self, ticker: str) -> str:
        return "{}"

    @override
    def _download_profile(self, ticker: str) -> str:
        return "{}"

    @override
    def _download_news(self, ticker: str, from_date: date, to_date: date) -> str:
        self.asked["news"] = (from_date, to_date)
        return "[]"

    @override
    def _download_earnings(self, ticker: str, from_date: date, to_date: date) -> str:
        self.asked["earnings"] = (from_date, to_date)
        return "{}"


def agent_over(
    graph: InMemoryGraphStore,
    source: object,
    settings: ProviderSettings | None = None,
) -> ProviderAgent:
    """A provider over *graph* and *source* (optionally with *settings*)."""
    return ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=source,  # type: ignore[arg-type]
        settings=settings,
    )


def run_request(
    graph: InMemoryGraphStore,
    as_of: object,
    *,
    tickers: tuple[str, ...] = ("AAPL",),
    lookback_days: int = 365,
    required_bars: int = 200,
) -> Node:
    """A RunRequest holding *as_of* under the contract's name, as dispatched."""
    props: dict[str, object] = {
        "run_id": "r1",
        "tickers": list(tickers),
        RUN_REQUEST_LOOKBACK_DAYS_PROP: lookback_days,
        RUN_REQUEST_REQUIRED_HISTORY_BARS_PROP: required_bars,
    }
    if as_of is not None:
        props[RUN_REQUEST_REQUESTED_AT_PROP] = as_of
    return graph.merge_node(RUN_REQUEST_LABEL, "run-request:r1", props)


def window_ends(graph: InMemoryGraphStore) -> tuple[str, str]:
    """The stored MarketData and RegimeContext ``window_end`` of run r1."""
    market = graph.get_node(MARKET_DATA_LABEL, "market-data:r1")
    regime = graph.get_node(REGIME_CONTEXT_LABEL, "regime-context:r1")
    assert market is not None
    assert regime is not None
    return str(market.props["window_end"]), str(regime.props["window_end"])
