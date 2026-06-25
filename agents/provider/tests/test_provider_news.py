"""ProviderAgent news field-gating and degraded-path tests.

Agent: provider
Role: verify get_market_data populates/gates news and degrades cleanly.
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
        sender="analyst",
        recipient="provider",
        message_type="request",
        capability="get_market_data",
        payload=payload,
    )


def _payload(*, news: bool) -> dict[str, object]:
    payload: dict[str, object] = {
        "tickers": ("AAPL",),
        "window": {"start": date(2026, 1, 1), "end": date(2026, 1, 3)},
    }
    if news:
        payload["fields"] = ("ohlcv", "news")
    return payload


def test_news_populated_when_field_requested() -> None:
    """PROV-IN-01 / PROV-OUT-01 / PROV-NEV-08: raw headlines served when news is
    requested; provider performs no sentiment scoring or classification."""
    bus = InProcessBus()
    ProviderAgent(
        bus,
        graph=InMemoryGraphStore(),
        source=FakeDataSource(
            bars=(_bar("AAPL", 1), _bar("AAPL", 2)),
            news={"AAPL": ("Headline A", "Headline B"), "MSFT": ("Other",)},
        ),
    ).bind()

    response = bus.request(_message(_payload(news=True)))

    assert response.payload["bars"][0]["ticker"] == "AAPL"
    assert response.payload["news"] == {"AAPL": ["Headline A", "Headline B"]}


def test_news_empty_by_default() -> None:
    """PROV-IN-01: news NOT in the field set → empty dict; field-gating enforced."""
    bus = InProcessBus()
    ProviderAgent(
        bus,
        graph=InMemoryGraphStore(),
        source=FakeDataSource(
            bars=(_bar("AAPL", 1),),
            news={"AAPL": ("Headline A",)},
        ),
    ).bind()

    response = bus.request(_message(_payload(news=False)))

    assert response.payload["news"] == {}


def test_news_failure_notes_without_tainting_ohlcv() -> None:
    """PROV-FAIL-02 / PROV-NEV-01 / PROV-OBS-02: a news failure is recorded as a note
    but does NOT set used_fallback (DRIFT-012); OHLCV is unaffected; fault is routed."""
    bus = InProcessBus()
    sink = CollectingFaultSink()
    ProviderAgent(
        bus,
        graph=InMemoryGraphStore(),
        source=FakeDataSource(
            bars=(_bar("AAPL", 1), _bar("AAPL", 2)),
            fail_news=True,
        ),
        sink=sink,
    ).bind()

    response = bus.request(_message(_payload(news=True)))

    quality = response.payload["quality"]
    assert response.payload["news"] == {}
    assert "news_degraded" in quality["notes"]
    assert quality["used_fallback"] is False  # DRIFT-012: enrichment doesn't taint
    assert response.payload["bars"][0]["ticker"] == "AAPL"
    assert len(sink.faults) == 1
    assert response.payload["provenance"]["graph_node_id"]
