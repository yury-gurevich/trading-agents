"""Alpha Vantage sentiment source tests.

Agent: provider
Role: verify NEWS_SENTIMENT parsing, per-ticker aggregation, 0-1 alignment, and
malformed-payload tolerance — all without network.
External I/O: none.
"""

from __future__ import annotations

import json
from datetime import date
from types import MethodType

import pytest

from agents.provider.av_sentiment import AlphaVantageSentimentSource
from contracts.common import Window

_WINDOW = Window(start=date(2026, 1, 1), end=date(2026, 1, 31))


def _stub(payload: str) -> AlphaVantageSentimentSource:
    source = AlphaVantageSentimentSource(
        api_key="k", base_url="https://av.test", timeout=10
    )

    def fake_download(
        _self: AlphaVantageSentimentSource, _tickers: tuple[str, ...]
    ) -> str:
        return payload

    source._download = MethodType(fake_download, source)  # type: ignore[method-assign]
    return source


def test_parses_and_aligns_mean_sentiment() -> None:
    payload = json.dumps(
        {
            "feed": [
                {
                    "ticker_sentiment": [
                        {"ticker": "AAPL", "ticker_sentiment_score": "0.4"},
                        {"ticker": "MSFT", "ticker_sentiment_score": "0.0"},
                    ]
                },
                {
                    "ticker_sentiment": [
                        {"ticker": "AAPL", "ticker_sentiment_score": "0.6"}
                    ]
                },
            ]
        }
    )
    scores = _stub(payload).fetch_sentiment(("AAPL", "MSFT"))
    # AAPL mean (0.4+0.6)/2 = 0.5 -> (0.5+1)/2 = 0.75 ; MSFT 0.0 -> 0.5
    assert scores == {"AAPL": 0.75, "MSFT": 0.5}


def test_filters_unrequested_and_malformed_entries() -> None:
    payload = json.dumps(
        {
            "feed": [
                {
                    "ticker_sentiment": [
                        {"ticker": "AAPL", "ticker_sentiment_score": "0.2"},
                        {"ticker": "TSM", "ticker_sentiment_score": "0.9"},
                        {"ticker": "AAPL", "ticker_sentiment_score": "oops"},
                        "not-a-dict",
                    ]
                },
                "not-an-article",
            ]
        }
    )
    scores = _stub(payload).fetch_sentiment(("AAPL",))
    assert set(scores) == {"AAPL"}
    assert scores["AAPL"] == pytest.approx(0.6)  # only the 0.2 reading -> (0.2+1)/2


def test_non_dict_payload_or_no_feed_yields_empty() -> None:
    assert _stub("[]").fetch_sentiment(("AAPL",)) == {}
    info = json.dumps({"Information": "premium"})
    assert _stub(info).fetch_sentiment(("AAPL",)) == {}
    assert _stub(json.dumps({"feed": "nope"})).fetch_sentiment(("AAPL",)) == {}


def test_empty_tickers_short_circuits() -> None:
    assert _stub("{}").fetch_sentiment(()) == {}


def test_av_source_serves_sentiment_only() -> None:
    source = AlphaVantageSentimentSource(
        api_key="k", base_url="https://av.test", timeout=10
    )
    assert source.fetch_ohlcv(("AAPL",), _WINDOW) == ()
    assert source.fetch_fundamentals(("AAPL",), _WINDOW) == {}
    assert source.fetch_news(("AAPL",), _WINDOW) == {}
    assert source.fetch_regime_inputs(date(2026, 1, 2)).vix is None
