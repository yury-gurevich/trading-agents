"""Finnhub pacing and per-ticker feed degradation tests.

Agent: provider
Role: prove request pacing, attributed optional-feed notes, and DRIFT-012.
External I/O: none.
"""

from __future__ import annotations

import json
from datetime import date
from email.message import Message
from types import MethodType
from urllib.error import HTTPError

from agents.provider.finnhub_resilience import RequestRateBudget
from agents.provider.fundamentals import FinnhubDataSource
from contracts.common import Window

_WINDOW = Window(start=date(2026, 1, 1), end=date(2026, 1, 3))


def _source(*, cap: int = 2) -> FinnhubDataSource:
    return FinnhubDataSource(
        api_key="k",
        base_url="https://x",
        timeout=5,
        request_budget_per_minute=0,
        degraded_note_ticker_cap=cap,
    )


def test_request_rate_budget_truth_table() -> None:
    """DRIFT-021: under-budget bursts pass; N+1 waits; 0 disables pacing."""
    now = 0.0
    sleeps: list[float] = []

    def clock() -> float:
        return now

    def sleep(seconds: float) -> None:
        nonlocal now
        sleeps.append(seconds)
        now += seconds

    budget = RequestRateBudget(2, clock=clock, sleep=sleep)
    budget.wait()
    budget.wait()
    assert sleeps == []

    budget.wait()
    assert sleeps == [60.0]

    disabled = RequestRateBudget(0, clock=clock, sleep=sleep)
    disabled.wait()
    disabled.wait()
    assert sleeps == [60.0]


def test_fundamentals_failure_is_per_ticker_and_bounded() -> None:
    source = _source(cap=2)

    def fake_download(_self: FinnhubDataSource, ticker: str) -> str:
        if ticker.startswith("BAD"):
            raise RuntimeError("rate limited")
        return json.dumps({"metric": {"peTTM": 30.0}})

    source._download = MethodType(fake_download, source)  # type: ignore[method-assign]

    result = source.fetch_fundamentals(
        ("AAPL", "BAD1", "MSFT", "BAD2", "BAD3"), _WINDOW
    )

    assert result == {"AAPL": {"peTTM": 30.0}, "MSFT": {"peTTM": 30.0}}
    assert source.consume_degraded_feed_notes() == (
        "fundamentals_degraded:3:BAD1,BAD2:RuntimeError",
    )
    assert source.consume_degraded_feed_notes() == ()


def test_news_failure_records_http_status_without_losing_successes() -> None:
    source = _source()

    def fake_download_news(
        _self: FinnhubDataSource, ticker: str, from_date: object, to_date: object
    ) -> str:
        if ticker == "RATE":
            raise HTTPError("url", 429, "Too Many Requests", hdrs=Message(), fp=None)
        return json.dumps([{"headline": f"{ticker} headline"}])

    source._download_news = MethodType(fake_download_news, source)  # type: ignore[method-assign]

    assert source.fetch_news(("AAPL", "RATE", "MSFT"), _WINDOW) == {
        "AAPL": ("AAPL headline",),
        "MSFT": ("MSFT headline",),
    }
    assert source.consume_degraded_feed_notes() == ("news_degraded:1:RATE:429",)


def test_sector_failure_is_per_ticker() -> None:
    source = _source()

    def fake_download_profile(_self: FinnhubDataSource, ticker: str) -> str:
        if ticker == "BAD":
            raise RuntimeError("profile failed")
        return json.dumps({"finnhubIndustry": "Technology"})

    source._download_profile = MethodType(fake_download_profile, source)  # type: ignore[method-assign]

    assert source.fetch_sectors(("AAPL", "BAD", "MSFT")) == {
        "AAPL": "Technology",
        "MSFT": "Technology",
    }
    assert source.consume_degraded_feed_notes() == (
        "sectors_degraded:1:BAD:RuntimeError",
    )


def test_earnings_failure_is_per_ticker() -> None:
    source = _source()

    def fake_download_earnings(
        _self: FinnhubDataSource, ticker: str, from_date: date, to_date: date
    ) -> str:
        if ticker == "BAD":
            raise RuntimeError("earnings failed")
        return json.dumps({"earningsCalendar": [{"date": "2026-01-25"}]})

    source._download_earnings = MethodType(fake_download_earnings, source)  # type: ignore[method-assign]

    assert source.fetch_earnings(("AAPL", "BAD", "MSFT"), _WINDOW) == {
        "AAPL": date(2026, 1, 25),
        "MSFT": date(2026, 1, 25),
    }
    assert source.consume_degraded_feed_notes() == (
        "earnings_degraded:1:BAD:RuntimeError",
    )
