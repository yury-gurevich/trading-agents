"""Provider source adapter tests.

Agent: provider
Role: verify deterministic source adapters and optional Stooq integration.
External I/O: optional HTTPS call to Stooq when STOOQ_TEST_NETWORK=1.
"""

from __future__ import annotations

import json
import os
from datetime import date
from types import MethodType

import pytest

from agents.provider.composite import CompositeDataSource
from agents.provider.fundamentals import (
    _FUNDAMENTAL_KEYS,
    FinnhubDataSource,
    _parse_metrics,
)
from agents.provider.sources import FakeDataSource
from contracts.common import Window

_WINDOW = Window(start=date(2024, 1, 2), end=date(2024, 1, 3))


def test_fake_source_fetches_and_fails_sentiment() -> None:
    source = FakeDataSource(sentiment={"AAPL": 0.6, "MSFT": 0.3})
    assert source.fetch_sentiment(("AAPL",)) == {"AAPL": 0.6}

    failing = FakeDataSource(fail_sentiment=True)
    with pytest.raises(RuntimeError, match="sentiment source unavailable"):
        failing.fetch_sentiment(("AAPL",))


def test_parse_metrics_extracts_target_keys_and_drops_the_rest() -> None:
    raw = json.dumps(
        {
            "metric": {
                "peBasicExclExtraTTM": 28.5,
                "peTTM": 30,
                "roeTTM": 0.42,
                "netProfitMarginTTM": 0.25,
                "currentRatioQuarterly": 1.1,
                "pbQuarterly": 12.0,
                "pbAnnual": 11.5,
                "totalDebt/totalEquityQuarterly": 1.8,
                "totalDebt/totalEquityAnnual": 1.6,
                "epsGrowthTTMYoy": 9.3,
                "revenueGrowthTTMYoy": 7.1,
                "marketCapitalization": None,
                "someText": "n/a",
                "ignoredFlag": True,
                "nonTargetNumber": 999,
            },
            "symbol": "AAPL",
        }
    )

    metrics = _parse_metrics(raw)

    assert set(metrics) == set(_FUNDAMENTAL_KEYS)
    assert metrics["peTTM"] == 30.0
    assert isinstance(metrics["peTTM"], float)
    assert "marketCapitalization" not in metrics
    assert "someText" not in metrics
    assert "ignoredFlag" not in metrics
    assert "nonTargetNumber" not in metrics


def test_parse_metrics_drops_none_and_non_numeric_target_values() -> None:
    raw = json.dumps(
        {"metric": {"peTTM": None, "roeTTM": "n/a", "netProfitMarginTTM": 0.2}}
    )

    assert _parse_metrics(raw) == {"netProfitMarginTTM": 0.2}


def test_parse_metrics_missing_or_empty_metric_object_yields_empty() -> None:
    assert _parse_metrics(json.dumps({"symbol": "AAPL"})) == {}
    assert _parse_metrics(json.dumps({"metric": None})) == {}
    assert _parse_metrics(json.dumps({"metric": "oops"})) == {}
    assert _parse_metrics(json.dumps([1, 2, 3])) == {}


def test_fake_source_returns_per_ticker_fundamentals_subset() -> None:
    source = FakeDataSource(
        fundamentals={"AAPL": {"peTTM": 30.0}, "MSFT": {"roeTTM": 0.4}}
    )

    assert source.fetch_fundamentals(("AAPL",), _WINDOW) == {"AAPL": {"peTTM": 30.0}}
    assert source.fetch_fundamentals(("TSLA",), _WINDOW) == {}


def test_fake_source_raises_when_fundamentals_fail() -> None:
    source = FakeDataSource(fail_fundamentals=True)

    with pytest.raises(RuntimeError, match="fundamentals source unavailable"):
        source.fetch_fundamentals(("AAPL",), _WINDOW)


def test_composite_routes_each_call_to_the_right_source() -> None:
    price = FakeDataSource(vix=12.0, fundamentals={"AAPL": {"peTTM": 1.0}})
    funda = FakeDataSource(vix=99.0, fundamentals={"AAPL": {"roeTTM": 0.4}})
    senti = FakeDataSource(sentiment={"AAPL": 0.7})
    composite = CompositeDataSource(price, funda, senti)

    assert composite.fetch_regime_inputs(date(2024, 1, 2)).vix == 12.0
    assert composite.fetch_ohlcv(("AAPL",), _WINDOW) == ()
    assert composite.fetch_fundamentals(("AAPL",), _WINDOW) == {"AAPL": {"roeTTM": 0.4}}
    assert composite.fetch_sentiment(("AAPL",)) == {"AAPL": 0.7}


def test_finnhub_source_parses_metrics_and_skips_empty_without_network() -> None:
    source = FinnhubDataSource(api_key="k", base_url="https://x", timeout=5)

    def fake_download(_self: FinnhubDataSource, ticker: str) -> str:
        if ticker == "AAPL":
            return json.dumps({"metric": {"peTTM": 30, "junk": "x"}})
        return json.dumps({"metric": {}})

    source._download = MethodType(fake_download, source)  # type: ignore[method-assign]

    assert source.fetch_ohlcv(("AAPL",), _WINDOW) == ()
    assert source.fetch_regime_inputs(date(2024, 1, 2)).vix is None
    assert source.fetch_sentiment(("AAPL",)) == {}
    assert source.fetch_fundamentals(("AAPL", "MSFT"), _WINDOW) == {
        "AAPL": {"peTTM": 30.0}
    }


@pytest.mark.integration
def test_finnhub_source_fetches_real_metrics_when_network_enabled() -> None:
    if os.getenv("FINNHUB_TEST_NETWORK") != "1":
        pytest.skip("FINNHUB_TEST_NETWORK=1 is not set")

    from agents.provider.fundamentals import FinnhubDataSource

    source = FinnhubDataSource(
        api_key=os.environ["FINNHUB_API_KEY"],
        base_url="https://finnhub.io/api/v1",
        timeout=10,
    )

    assert source.fetch_fundamentals(("AAPL",), _WINDOW)
