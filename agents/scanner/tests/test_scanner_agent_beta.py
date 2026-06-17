"""Scanner agent beta-cap end-to-end tests.

Agent: scanner
Role: verify the scanner fetches a benchmark and applies the beta cap over the bus.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from agents.provider import ProviderAgent
from agents.provider.sources import FakeDataSource
from agents.scanner import ScannerAgent
from agents.scanner.provider_client import request_benchmark_bars
from agents.scanner.settings import ScannerSettings
from agents.scanner.universe import FakeUniverse
from contracts.common import Window
from contracts.provider import OHLCVBar
from kernel import AgentMessage, CollectingFaultSink, InMemoryGraphStore, InProcessBus


def _bar(ticker: str, days_ago: int, close: float) -> OHLCVBar:
    day = datetime.now(tz=UTC).date() - timedelta(days=days_ago)
    open_ = close * 0.99
    return OHLCVBar(
        ticker=ticker,
        bar_date=day,
        open=open_,
        high=max(open_, close) + 1.0,
        low=min(open_, close) - 1.0,
        close=close,
        volume=1_000_000,
    )


def _series(ticker: str, closes: list[float]) -> tuple[OHLCVBar, ...]:
    count = len(closes)
    return tuple(_bar(ticker, count - 1 - i, close) for i, close in enumerate(closes))


def _request() -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="scanner",
        message_type="request",
        capability="run_scan",
        payload={"run_id": "scan-beta", "universe": "fixture"},
    )


def test_scan_drops_the_high_beta_name_and_keeps_beta_on_survivors() -> None:
    bars = (
        *_series("SPY", [100.0, 110.0, 132.0]),
        *_series("LOWB", [100.0, 110.0, 132.0]),  # beta 1.0
        *_series("HIGHB", [100.0, 120.0, 168.0]),  # beta 2.0 > cap
    )
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    ProviderAgent(bus, graph=graph, source=FakeDataSource(bars=bars)).bind()
    ScannerAgent(
        bus,
        graph=graph,
        universe=FakeUniverse({"fixture": ("LOWB", "HIGHB")}),
        settings=ScannerSettings(
            min_relative_strength=0.02,
            min_price=5.0,
            min_average_volume=500_000.0,
            candidate_cap=5,
            lookback_days=7,
            benchmark_ticker="SPY",
            max_beta=1.5,
            beta_min_observations=2,
        ),
        sink=sink,
    ).bind()

    payload = bus.request(_request()).payload

    assert [candidate["ticker"] for candidate in payload["candidates"]] == ["LOWB"]
    assert payload["filter_trace"]["dropped_by_filter"] == {"max_beta": 1}
    assert round(payload["candidates"][0]["metrics"]["beta"], 6) == 1.0
    assert sink.faults == []


def test_request_benchmark_bars_returns_empty_without_a_provider() -> None:
    end = datetime.now(tz=UTC).date()
    window = Window(start=end - timedelta(days=7), end=end)
    bars = request_benchmark_bars(InProcessBus(), CollectingFaultSink(), "SPY", window)
    assert bars == ()
