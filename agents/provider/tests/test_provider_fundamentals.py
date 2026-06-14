"""ProviderAgent fundamentals field-gating and degraded-path tests.

Agent: provider
Role: verify get_market_data populates/gates fundamentals and degrades cleanly.
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


def _payload(*, fundamentals: bool) -> dict[str, object]:
    payload: dict[str, object] = {
        "tickers": ("AAPL",),
        "window": {"start": date(2026, 1, 1), "end": date(2026, 1, 3)},
    }
    if fundamentals:
        payload["fields"] = ("ohlcv", "fundamentals")
    return payload


def test_fundamentals_populated_when_field_requested() -> None:
    bus = InProcessBus()
    ProviderAgent(
        bus,
        graph=InMemoryGraphStore(),
        source=FakeDataSource(
            bars=(_bar("AAPL", 1), _bar("AAPL", 2)),
            fundamentals={"AAPL": {"peTTM": 30.0}, "MSFT": {"roeTTM": 0.4}},
        ),
    ).bind()

    response = bus.request(_message(_payload(fundamentals=True)))

    assert response.payload["bars"][0]["ticker"] == "AAPL"
    assert response.payload["fundamentals"] == {"AAPL": {"peTTM": 30.0}}


def test_fundamentals_empty_by_default() -> None:
    bus = InProcessBus()
    ProviderAgent(
        bus,
        graph=InMemoryGraphStore(),
        source=FakeDataSource(
            bars=(_bar("AAPL", 1),),
            fundamentals={"AAPL": {"peTTM": 30.0}},
        ),
    ).bind()

    response = bus.request(_message(_payload(fundamentals=False)))

    assert response.payload["fundamentals"] == {}


def test_fundamentals_failure_degrades_without_affecting_ohlcv() -> None:
    bus = InProcessBus()
    sink = CollectingFaultSink()
    ProviderAgent(
        bus,
        graph=InMemoryGraphStore(),
        source=FakeDataSource(
            bars=(_bar("AAPL", 1), _bar("AAPL", 2)),
            fail_fundamentals=True,
        ),
        sink=sink,
    ).bind()

    response = bus.request(_message(_payload(fundamentals=True)))

    quality = response.payload["quality"]
    assert response.payload["fundamentals"] == {}
    assert "fundamentals_degraded" in quality["notes"]
    assert quality["used_fallback"] is True
    assert response.payload["bars"][0]["ticker"] == "AAPL"
    assert len(sink.faults) == 1
    assert response.payload["provenance"]["graph_node_id"]
