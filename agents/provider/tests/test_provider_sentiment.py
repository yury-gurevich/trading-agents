"""ProviderAgent sentiment field-gating and degraded-path tests.

Agent: provider
Role: verify get_market_data populates/gates vendor sentiment and degrades cleanly.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

from agents.provider import ProviderAgent
from agents.provider.sources import FakeDataSource
from contracts.provider import OHLCVBar
from kernel import AgentMessage, CollectingFaultSink, InMemoryGraphStore, InProcessBus


def _bar(ticker: str, day: int) -> OHLCVBar:
    return OHLCVBar(
        ticker=ticker,
        bar_date=date(2026, 1, day),
        open=100.0,
        high=102.0,
        low=99.0,
        close=101.0,
        volume=1000,
    )


def _message(payload: dict[str, object]) -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="provider",
        message_type="request",
        capability="get_market_data",
        payload=payload,
    )


def _payload(*, sentiment: bool) -> dict[str, object]:
    payload: dict[str, object] = {
        "tickers": ("AAPL",),
        "window": {"start": date(2026, 1, 1), "end": date(2026, 1, 3)},
    }
    if sentiment:
        payload["fields"] = ("ohlcv", "sentiment")
    return payload


def test_sentiment_populated_when_field_requested() -> None:
    bus = InProcessBus()
    ProviderAgent(
        bus,
        graph=InMemoryGraphStore(),
        source=FakeDataSource(
            bars=(_bar("AAPL", 1), _bar("AAPL", 2)),
            sentiment={"AAPL": 0.58, "MSFT": 0.40},
        ),
    ).bind()

    response = bus.request(_message(_payload(sentiment=True)))

    assert response.payload["bars"][0]["ticker"] == "AAPL"
    assert response.payload["sentiment"] == {"AAPL": 0.58}


def test_sentiment_empty_by_default() -> None:
    bus = InProcessBus()
    ProviderAgent(
        bus,
        graph=InMemoryGraphStore(),
        source=FakeDataSource(
            bars=(_bar("AAPL", 1),),
            sentiment={"AAPL": 0.58},
        ),
    ).bind()

    response = bus.request(_message(_payload(sentiment=False)))

    assert response.payload["sentiment"] == {}


def test_sentiment_failure_degrades_without_affecting_ohlcv() -> None:
    bus = InProcessBus()
    sink = CollectingFaultSink()
    ProviderAgent(
        bus,
        graph=InMemoryGraphStore(),
        source=FakeDataSource(
            bars=(_bar("AAPL", 1), _bar("AAPL", 2)),
            fail_sentiment=True,
        ),
        sink=sink,
    ).bind()

    response = bus.request(_message(_payload(sentiment=True)))

    quality = response.payload["quality"]
    assert response.payload["sentiment"] == {}
    assert "sentiment_degraded" in quality["notes"]
    assert quality["used_fallback"] is True
    assert response.payload["bars"][0]["ticker"] == "AAPL"
    assert len(sink.faults) == 1
    assert response.payload["provenance"]["graph_node_id"]
