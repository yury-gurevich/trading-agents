"""Finnhub company-news parser and news source adapter tests.

Agent: provider
Role: verify _parse_news and news source adapters.
External I/O: none.
"""

from __future__ import annotations

import json
from datetime import date
from types import MethodType

import pytest

from agents.provider.composite import CompositeDataSource
from agents.provider.fundamentals import FinnhubDataSource, _parse_news
from agents.provider.sources import FakeDataSource
from agents.provider.stooq import StooqDataSource
from contracts.common import Window

_WINDOW = Window(start=date(2024, 1, 2), end=date(2024, 1, 3))


def _make_article(headline: str) -> dict[str, object]:
    return {"headline": headline, "summary": "summary", "source": "reuters"}


def test_parse_news_extracts_headlines_in_order() -> None:
    raw = json.dumps(
        [
            _make_article("Headline A"),
            _make_article("Headline B"),
            _make_article("Headline C"),
        ]
    )

    result = _parse_news(raw, cap=10)

    assert result == ("Headline A", "Headline B", "Headline C")


def test_parse_news_cap_trims_long_array() -> None:
    articles = [_make_article(f"Headline {i}") for i in range(30)]
    raw = json.dumps(articles)

    result = _parse_news(raw, cap=5)

    assert len(result) == 5
    assert result == tuple(f"Headline {i}" for i in range(5))


def test_parse_news_drops_missing_headline_field() -> None:
    raw = json.dumps([{"summary": "no headline here"}, _make_article("Good")])

    assert _parse_news(raw, cap=10) == ("Good",)


def test_parse_news_drops_empty_or_non_string_headline() -> None:
    raw = json.dumps(
        [{"headline": ""}, {"headline": 42}, {"headline": None}, _make_article("OK")]
    )

    assert _parse_news(raw, cap=10) == ("OK",)


def test_parse_news_non_array_or_malformed_payload_returns_empty() -> None:
    assert _parse_news(json.dumps({"headline": "oops"}), cap=10) == ()
    assert _parse_news(json.dumps(42), cap=10) == ()
    assert _parse_news("not json at all", cap=10) == ()
    assert _parse_news("", cap=5) == ()


def test_parse_news_non_dict_items_are_skipped() -> None:
    raw = json.dumps(["not a dict", 123, None, _make_article("Valid")])

    assert _parse_news(raw, cap=10) == ("Valid",)


def test_parse_news_empty_array_returns_empty() -> None:
    assert _parse_news(json.dumps([]), cap=10) == ()


def test_parse_news_never_raises_on_garbage_input() -> None:
    for bad in ["null", json.dumps(None), json.dumps(False)]:
        assert isinstance(_parse_news(bad, cap=10), tuple)


def test_stooq_source_returns_empty_news() -> None:
    assert StooqDataSource().fetch_news(("AAPL",), _WINDOW) == {}


def test_fake_source_returns_per_ticker_news_subset() -> None:
    source = FakeDataSource(
        news={"AAPL": ("Headline A", "Headline B"), "MSFT": ("Other",)}
    )

    assert source.fetch_news(("AAPL",), _WINDOW) == {
        "AAPL": ("Headline A", "Headline B")
    }
    assert source.fetch_news(("TSLA",), _WINDOW) == {}


def test_fake_source_raises_when_news_fails() -> None:
    with pytest.raises(RuntimeError, match="news source unavailable"):
        FakeDataSource(fail_news=True).fetch_news(("AAPL",), _WINDOW)


def test_finnhub_source_fetches_news_and_skips_empty_without_network() -> None:
    source = FinnhubDataSource(api_key="k", base_url="https://x", timeout=5)

    def fake_download_news(
        _self: FinnhubDataSource, ticker: str, from_date: object, to_date: object
    ) -> str:
        if ticker == "AAPL":
            return json.dumps([{"headline": "Big news"}, {"headline": "More news"}])
        return json.dumps([])

    source._download_news = MethodType(fake_download_news, source)  # type: ignore[method-assign]

    result = source.fetch_news(("AAPL", "MSFT"), _WINDOW)

    assert result == {"AAPL": ("Big news", "More news")}


def test_composite_routes_news_to_fundamentals_source() -> None:
    price = FakeDataSource(news={"AAPL": ("price-side",)})
    funda = FakeDataSource(news={"AAPL": ("funda-side",)})
    senti = FakeDataSource()
    result = CompositeDataSource(price, funda, senti).fetch_news(("AAPL",), _WINDOW)
    assert result == {"AAPL": ("funda-side",)}
