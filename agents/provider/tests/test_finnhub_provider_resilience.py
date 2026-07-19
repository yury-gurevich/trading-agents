"""Provider-path Finnhub degradation regression tests.

Agent: provider
Role: prove attributed Finnhub enrichment faults do not taint clean OHLCV.
External I/O: none.
"""

from __future__ import annotations

import json
from datetime import date
from types import MethodType

from agents.provider import ProviderAgent
from agents.provider.composite import CompositeDataSource
from agents.provider.fundamentals import FinnhubDataSource
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from contracts.common import Window
from contracts.provider import DataRequest, OHLCVBar
from kernel import InMemoryGraphStore, InProcessBus

_WINDOW = Window(start=date(2026, 1, 1), end=date(2026, 1, 3))


def _bar(ticker: str) -> OHLCVBar:
    return OHLCVBar(
        ticker=ticker,
        bar_date=date(2026, 1, 2),
        open=100.0,
        high=102.0,
        low=99.0,
        close=101.0,
        volume=1000,
    )


def test_provider_attributed_enrichment_faults_do_not_set_used_fallback() -> None:
    """DRIFT-012: optional enrichment faults never taint clean OHLCV."""
    finnhub = FinnhubDataSource(
        api_key="k",
        base_url="https://x",
        timeout=5,
        request_budget_per_minute=0,
        degraded_note_ticker_cap=1,
    )

    def fail_bad(ticker: str) -> None:
        if ticker == "BAD":
            raise RuntimeError("rate limited")

    def fake_download(_self: FinnhubDataSource, ticker: str) -> str:
        fail_bad(ticker)
        return json.dumps({"metric": {"peTTM": 30.0}})

    def fake_download_news(
        _self: FinnhubDataSource, ticker: str, from_date: object, to_date: object
    ) -> str:
        fail_bad(ticker)
        return json.dumps([{"headline": f"{ticker} headline"}])

    def fake_download_profile(_self: FinnhubDataSource, ticker: str) -> str:
        fail_bad(ticker)
        return json.dumps({"finnhubIndustry": "Technology"})

    def fake_download_earnings(
        _self: FinnhubDataSource, ticker: str, from_date: date, to_date: date
    ) -> str:
        fail_bad(ticker)
        return json.dumps({"earningsCalendar": [{"date": "2026-01-25"}]})

    finnhub._download = MethodType(fake_download, finnhub)  # type: ignore[method-assign]
    finnhub._download_news = MethodType(fake_download_news, finnhub)  # type: ignore[method-assign]
    finnhub._download_profile = MethodType(fake_download_profile, finnhub)  # type: ignore[method-assign]
    finnhub._download_earnings = MethodType(fake_download_earnings, finnhub)  # type: ignore[method-assign]
    source = CompositeDataSource(
        FakeDataSource(bars=(_bar("AAPL"), _bar("BAD"))),
        finnhub,
        FakeDataSource(),
    )
    agent = ProviderAgent(
        InProcessBus(),
        graph=InMemoryGraphStore(),
        source=source,
        settings=ProviderSettings(max_staleness_days=7),
    )

    market = agent._get_market_data(
        DataRequest(
            tickers=("AAPL", "BAD"),
            window=_WINDOW,
            fields=("ohlcv", "fundamentals", "news", "sectors", "earnings_calendar"),
        )
    )

    assert market.quality.used_fallback is False
    assert market.fundamentals == {"AAPL": {"peTTM": 30.0}}
    assert market.news == {"AAPL": ("AAPL headline",)}
    assert market.sectors == {"AAPL": "Technology"}
    assert market.earnings == {"AAPL": date(2026, 1, 25)}
    assert market.quality.notes == (
        "fundamentals_degraded:1:BAD:RuntimeError",
        "news_degraded:1:BAD:RuntimeError",
        "sectors_degraded:1:BAD:RuntimeError",
        "earnings_degraded:1:BAD:RuntimeError",
    )
