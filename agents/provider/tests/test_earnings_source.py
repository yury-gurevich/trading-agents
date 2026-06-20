"""Finnhub next-earnings parser + earnings feed adapter and field-gating tests.

Agent: provider
Role: verify _parse_next_earnings, every source's fetch_earnings, and the provider's
      ``earnings_calendar`` field-gate (served + degraded).
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
from agents.provider.fundamentals_parse import _parse_next_earnings
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from agents.provider.stooq import StooqDataSource
from agents.provider.tiingo import TiingoDataSource
from contracts.common import Window
from contracts.provider import DataRequest, MarketData
from kernel import AgentMessage, InMemoryGraphStore, InProcessBus

_WINDOW = Window(start=date(2024, 1, 2), end=date(2024, 1, 3))
_AS_OF = date(2024, 1, 3)


def _calendar(*dates: str) -> str:
    return json.dumps(
        {"earningsCalendar": [{"symbol": "AAPL", "date": d} for d in dates]}
    )


def test_parse_next_earnings_returns_earliest_upcoming_date() -> None:
    """PROV-TYP-01: the earnings parser selects the earliest upcoming date from a
    multi-date calendar."""
    raw = _calendar("2024-02-10", "2024-01-25", "2024-03-01")
    assert _parse_next_earnings(raw, _AS_OF) == date(2024, 1, 25)


def test_parse_next_earnings_includes_date_on_the_boundary() -> None:
    """PROV-TYP-01: as_of date itself is treated as upcoming (boundary-inclusive)."""
    assert _parse_next_earnings(_calendar("2024-01-03"), _AS_OF) == date(2024, 1, 3)


def test_parse_next_earnings_ignores_past_dates() -> None:
    """PROV-NEV-07: past earnings dates are discarded; None is returned when no future
    date exists — never fabricated."""
    assert _parse_next_earnings(_calendar("2023-12-20", "2024-01-01"), _AS_OF) is None


def test_parse_next_earnings_skips_bad_dates_and_non_dict_items() -> None:
    """PROV-NEV-07: malformed calendar items (non-dict, bad date strings, int dates)
    are skipped; valid entries still returned — never crashes."""
    raw = json.dumps(
        {
            "earningsCalendar": [
                "nope",
                {"date": "not-a-date"},
                {"date": 20240201},
                {"symbol": "AAPL"},
                {"date": "2024-02-01"},
            ]
        }
    )
    assert _parse_next_earnings(raw, _AS_OF) == date(2024, 2, 1)


def test_parse_next_earnings_malformed_or_empty_yields_none() -> None:
    """PROV-NEV-07 / PROV-TYP-03: malformed or empty earnings JSON yields None —
    never fabricated, never a crash."""
    assert _parse_next_earnings(json.dumps({"earningsCalendar": []}), _AS_OF) is None
    assert _parse_next_earnings(json.dumps({"other": 1}), _AS_OF) is None
    assert _parse_next_earnings(json.dumps([1, 2, 3]), _AS_OF) is None
    assert _parse_next_earnings("not json at all", _AS_OF) is None
    assert _parse_next_earnings("", _AS_OF) is None


def test_fake_source_returns_per_ticker_earnings_subset() -> None:
    """PROV-IN-01: the earnings source serves only the requested tickers' data —
    exact field-set, no extras."""
    source = FakeDataSource(
        earnings={"AAPL": date(2024, 1, 25), "XOM": date(2024, 2, 1)}
    )
    assert source.fetch_earnings(("AAPL",), _WINDOW) == {"AAPL": date(2024, 1, 25)}
    assert source.fetch_earnings(("TSLA",), _WINDOW) == {}


def test_fake_source_raises_when_earnings_fail() -> None:
    """PROV-FAIL-01: an earnings-source failure propagates as an exception to be
    contained at the agent boundary."""
    with pytest.raises(RuntimeError, match="earnings source unavailable"):
        FakeDataSource(fail_earnings=True).fetch_earnings(("AAPL",), _WINDOW)


def test_ohlcv_and_sentiment_only_sources_return_no_earnings() -> None:
    """PROV-IDN-02: OHLCV and sentiment-only sources return empty earnings — clean
    boundary separation; only the fundamentals source holds earnings data."""
    assert StooqDataSource().fetch_earnings(("AAPL",), _WINDOW) == {}
    tiingo = TiingoDataSource(api_key="k", base_url="https://x", timeout=10)
    assert tiingo.fetch_earnings(("AAPL",), _WINDOW) == {}
    fmp = FMPDataSource(api_key="k", base_url="https://x", timeout=10)
    assert fmp.fetch_earnings(("AAPL",), _WINDOW) == {}
    av = AlphaVantageSentimentSource(api_key="k", base_url="https://x", timeout=10)
    assert av.fetch_earnings(("AAPL",), _WINDOW) == {}


def test_finnhub_source_fetches_earnings_and_skips_unknown_without_network() -> None:
    """PROV-NEV-07: the Finnhub adapter skips tickers with no upcoming earnings —
    never fabricates a date for an unknown ticker."""
    source = FinnhubDataSource(api_key="k", base_url="https://x", timeout=5)

    def fake_download_earnings(
        _self: FinnhubDataSource, ticker: str, from_date: date, to_date: date
    ) -> str:
        if ticker == "AAPL":
            return _calendar("2024-01-25")
        return json.dumps({"earningsCalendar": []})

    source._download_earnings = MethodType(fake_download_earnings, source)  # type: ignore[method-assign]

    assert source.fetch_earnings(("AAPL", "MSFT"), _WINDOW) == {
        "AAPL": date(2024, 1, 25)
    }


def test_composite_routes_earnings_to_fundamentals_source() -> None:
    """PROV-IDN-01: the composite source routes earnings queries to the fundamentals
    sub-source (Finnhub), not the price feed."""
    price = FakeDataSource(earnings={"AAPL": date(2030, 1, 1)})
    funda = FakeDataSource(earnings={"AAPL": date(2024, 1, 25)})
    senti = FakeDataSource()
    result = CompositeDataSource(price, funda, senti).fetch_earnings(("AAPL",), _WINDOW)
    assert result == {"AAPL": date(2024, 1, 25)}


def _earnings_request() -> AgentMessage:
    return AgentMessage(
        sender="analyst",
        recipient="provider",
        message_type="request",
        capability="get_market_data",
        payload=DataRequest(
            tickers=("AAPL",), window=_WINDOW, fields=("earnings_calendar",)
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


def test_provider_serves_earnings_when_requested() -> None:
    """PROV-IN-01 / PROV-OUT-01: provider serves earnings_calendar field when
    requested; response contains the next earnings date per ticker."""
    bus = _wire(FakeDataSource(earnings={"AAPL": date(2024, 1, 25)}))
    market = MarketData.model_validate(bus.request(_earnings_request()).payload)
    assert market.earnings == {"AAPL": date(2024, 1, 25)}


def test_provider_degrades_when_an_earnings_fetch_faults() -> None:
    """PROV-FAIL-02 / PROV-NEV-01: an earnings-fetch fault degrades gracefully —
    flagged in quality notes; other fields unaffected."""
    bus = _wire(FakeDataSource(fail_earnings=True))
    market = MarketData.model_validate(bus.request(_earnings_request()).payload)
    assert market.earnings == {}
    assert "earnings_degraded" in market.quality.notes
    assert market.quality.used_fallback is True
