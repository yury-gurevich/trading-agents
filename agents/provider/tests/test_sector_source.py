"""Finnhub sector parser + sector feed adapter and field-gating tests.

Agent: provider
Role: verify _parse_sector, every source's fetch_sectors, and the provider's
      ``sectors`` field-gate (served + degraded).
External I/O: none.
"""

from __future__ import annotations

import json
from datetime import date
from types import MethodType

import pytest

from agents.provider import ProviderAgent
from agents.provider.av_sentiment import AlphaVantageSentimentSource
from agents.provider.composite import CompositeDataSource
from agents.provider.fmp import FMPDataSource
from agents.provider.fundamentals import FinnhubDataSource
from agents.provider.fundamentals_parse import _parse_sector
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from agents.provider.stooq import StooqDataSource
from agents.provider.tiingo import TiingoDataSource
from contracts.common import Window
from contracts.provider import DataRequest, MarketData
from kernel import AgentMessage, InMemoryGraphStore, InProcessBus

_WINDOW = Window(start=date(2024, 1, 2), end=date(2024, 1, 3))


def test_parse_sector_extracts_finnhub_industry() -> None:
    assert _parse_sector(json.dumps({"finnhubIndustry": "Technology"})) == "Technology"


def test_parse_sector_missing_empty_or_non_string_yields_none() -> None:
    assert _parse_sector(json.dumps({"name": "AAPL"})) is None
    assert _parse_sector(json.dumps({"finnhubIndustry": ""})) is None
    assert _parse_sector(json.dumps({"finnhubIndustry": 42})) is None


def test_parse_sector_non_dict_or_malformed_yields_none() -> None:
    assert _parse_sector(json.dumps([1, 2, 3])) is None
    assert _parse_sector("not json at all") is None
    assert _parse_sector("") is None


def test_fake_source_returns_per_ticker_sector_subset() -> None:
    source = FakeDataSource(sectors={"AAPL": "Technology", "XOM": "Energy"})
    assert source.fetch_sectors(("AAPL",)) == {"AAPL": "Technology"}
    assert source.fetch_sectors(("TSLA",)) == {}


def test_fake_source_raises_when_sectors_fail() -> None:
    with pytest.raises(RuntimeError, match="sectors source unavailable"):
        FakeDataSource(fail_sectors=True).fetch_sectors(("AAPL",))


def test_ohlcv_and_sentiment_only_sources_return_no_sectors() -> None:
    assert StooqDataSource().fetch_sectors(("AAPL",)) == {}
    tiingo = TiingoDataSource(api_key="k", base_url="https://x", timeout=10)
    assert tiingo.fetch_sectors(("AAPL",)) == {}
    fmp = FMPDataSource(api_key="k", base_url="https://x", timeout=10)
    assert fmp.fetch_sectors(("AAPL",)) == {}
    av = AlphaVantageSentimentSource(api_key="k", base_url="https://x", timeout=10)
    assert av.fetch_sectors(("AAPL",)) == {}


def test_finnhub_source_fetches_sectors_and_skips_unknown_without_network() -> None:
    source = FinnhubDataSource(api_key="k", base_url="https://x", timeout=5)

    def fake_download_profile(_self: FinnhubDataSource, ticker: str) -> str:
        if ticker == "AAPL":
            return json.dumps({"finnhubIndustry": "Technology"})
        return json.dumps({})

    source._download_profile = MethodType(fake_download_profile, source)  # type: ignore[method-assign]

    assert source.fetch_sectors(("AAPL", "MSFT")) == {"AAPL": "Technology"}


def test_composite_routes_sectors_to_fundamentals_source() -> None:
    price = FakeDataSource(sectors={"AAPL": "price-side"})
    funda = FakeDataSource(sectors={"AAPL": "Technology"})
    senti = FakeDataSource()
    result = CompositeDataSource(price, funda, senti).fetch_sectors(("AAPL",))
    assert result == {"AAPL": "Technology"}


def _sectors_request() -> AgentMessage:
    return AgentMessage(
        sender="analyst",
        recipient="provider",
        message_type="request",
        capability="get_market_data",
        payload=DataRequest(
            tickers=("AAPL",), window=_WINDOW, fields=("sectors",)
        ).model_dump(mode="json"),
    )


def _wire(source: FakeDataSource) -> InProcessBus:
    bus = InProcessBus()
    ProviderAgent(
        bus,
        graph=InMemoryGraphStore(),
        source=source,
        settings=ProviderSettings(max_staleness_days=7),
    ).bind()
    return bus


def test_provider_serves_sectors_when_requested() -> None:
    bus = _wire(FakeDataSource(sectors={"AAPL": "Technology"}))
    market = MarketData.model_validate(bus.request(_sectors_request()).payload)
    assert market.sectors == {"AAPL": "Technology"}


def test_provider_degrades_when_a_sector_fetch_faults() -> None:
    bus = _wire(FakeDataSource(fail_sectors=True))
    market = MarketData.model_validate(bus.request(_sectors_request()).payload)
    assert market.sectors == {}
    assert "sectors_degraded" in market.quality.notes
    assert market.quality.used_fallback is True
