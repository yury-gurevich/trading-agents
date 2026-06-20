"""ScannerAgent explain_filter capability tests.

Agent: scanner
Role: verify the explain_filter RPC returns a grounded Explanation.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from agents.provider import ProviderAgent
from agents.provider.sources import FakeDataSource
from agents.scanner import ScannerAgent
from agents.scanner.settings import ScannerSettings
from agents.scanner.universe import FakeUniverse
from contracts.provider import OHLCVBar
from kernel import AgentMessage, CollectingFaultSink, InMemoryGraphStore, InProcessBus


def _bar(ticker: str, days_ago: int, close: float, volume: int) -> OHLCVBar:
    day = datetime.now(tz=UTC).date() - timedelta(days=days_ago)
    open_ = close * 0.95
    return OHLCVBar(
        ticker=ticker,
        bar_date=day,
        open=open_,
        high=max(open_, close) + 1.0,
        low=min(open_, close) - 1.0,
        close=close,
        volume=volume,
    )


def _fixture_bars() -> tuple[OHLCVBar, ...]:
    return (
        _bar("AAPL", 5, 100.0, 1_000_000),
        _bar("AAPL", 0, 110.0, 1_200_000),
    )


def _wire() -> tuple[InProcessBus, InMemoryGraphStore, CollectingFaultSink]:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    ProviderAgent(bus, graph=graph, source=FakeDataSource(bars=_fixture_bars())).bind()
    ScannerAgent(
        bus,
        graph=graph,
        universe=FakeUniverse({"fixture": ("AAPL",)}),
        settings=ScannerSettings(min_price=5.0, min_average_volume=100_000),
        sink=sink,
    ).bind()
    return bus, graph, sink


def test_explain_filter_returns_grounded_explanation() -> None:
    """SCAN-OUT-05: explain_filter returns grounded Explanation; no provider call."""
    bus, _graph, _sink = _wire()
    msg = AgentMessage(
        sender="tester",
        recipient="scanner",
        message_type="request",
        capability="explain_filter",
        payload={"run_id": "explain-test", "universe": "fixture"},
    )

    response = bus.request(msg)

    assert response.message_type == "response"
    assert "relative strength" in response.payload["summary"]
    assert response.payload["evidence_refs"] == ["scanner.filters.core"]
