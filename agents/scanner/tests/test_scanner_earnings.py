"""Scanner earnings-window exclusion tests.

Agent: scanner
Role: verify the earnings-window drop / keep / dormant branches in the filter chain
      and the end-to-end gate over the bus (consumes provider MarketData.earnings).
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from agents.provider import ProviderAgent
from agents.provider.sources import FakeDataSource
from agents.scanner import ScannerAgent
from agents.scanner.domain.filters import _days_to_earnings, apply_filters
from agents.scanner.settings import ScannerSettings
from agents.scanner.universe import FakeUniverse
from contracts.provider import OHLCVBar
from kernel import AgentMessage, CollectingFaultSink, InMemoryGraphStore, InProcessBus

_AS_OF = date(2024, 6, 1)


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


def _settings() -> ScannerSettings:
    return ScannerSettings(
        min_relative_strength=0.02,
        min_price=5.0,
        min_average_volume=500_000.0,
        candidate_cap=5,
        lookback_days=7,
        earnings_exclusion_days=5,
    )


def test_days_to_earnings_handles_unknown_upcoming_and_past() -> None:
    earnings = {"SOON": date(2024, 6, 4), "PAST": date(2024, 5, 20)}
    assert _days_to_earnings("SOON", earnings, _AS_OF) == 3
    assert _days_to_earnings("PAST", earnings, _AS_OF) is None  # already reported
    assert _days_to_earnings("UNKNOWN", earnings, _AS_OF) is None


def test_earnings_within_window_drops_the_candidate() -> None:
    bars = _series("SOON", [100.0, 110.0, 132.0])
    earnings = {"SOON": date(2024, 6, 3)}  # 2 days out, <= 5
    survivors, trace = apply_filters(("SOON",), bars, (), earnings, _AS_OF, _settings())
    assert survivors == ()
    assert trace.dropped_by_filter == {"earnings_window": 1}


def test_earnings_on_the_exclusion_boundary_drops_the_candidate() -> None:
    bars = _series("EDGE", [100.0, 110.0, 132.0])
    earnings = {"EDGE": date(2024, 6, 6)}  # exactly 5 days out -> excluded (<=)
    survivors, trace = apply_filters(("EDGE",), bars, (), earnings, _AS_OF, _settings())
    assert survivors == ()
    assert trace.dropped_by_filter == {"earnings_window": 1}


def test_earnings_beyond_window_keeps_candidate_and_records_metric() -> None:
    bars = _series("FAR", [100.0, 110.0, 132.0])
    earnings = {"FAR": date(2024, 7, 1)}  # 30 days out
    survivors, trace = apply_filters(("FAR",), bars, (), earnings, _AS_OF, _settings())
    assert trace.dropped_by_filter == {}
    assert survivors[0].metrics["days_to_earnings"] == 30.0
    assert "earnings_window" in survivors[0].survived_filters


def test_no_earnings_data_keeps_candidate_dormant() -> None:
    bars = _series("NONE", [100.0, 110.0, 132.0])
    survivors, trace = apply_filters(("NONE",), bars, (), {}, _AS_OF, _settings())
    assert trace.dropped_by_filter == {}
    assert "days_to_earnings" not in survivors[0].metrics
    assert "earnings_window" not in survivors[0].survived_filters


def test_past_earnings_date_does_not_exclude() -> None:
    bars = _series("PAST", [100.0, 110.0, 132.0])
    earnings = {"PAST": date(2024, 5, 20)}  # before as-of -> treated as unknown
    survivors, trace = apply_filters(("PAST",), bars, (), earnings, _AS_OF, _settings())
    assert trace.dropped_by_filter == {}
    assert "days_to_earnings" not in survivors[0].metrics


def _request() -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="scanner",
        message_type="request",
        capability="run_scan",
        payload={"run_id": "scan-earnings", "universe": "fixture"},
    )


def test_scan_excludes_the_near_earnings_name_over_the_bus() -> None:
    today = datetime.now(tz=UTC).date()
    bars = (
        *_series("NEAR", [100.0, 110.0, 132.0]),
        *_series("FAR", [100.0, 110.0, 132.0]),
    )
    earnings = {"NEAR": today + timedelta(days=2), "FAR": today + timedelta(days=30)}
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    ProviderAgent(
        bus, graph=graph, source=FakeDataSource(bars=bars, earnings=earnings)
    ).bind()
    ScannerAgent(
        bus,
        graph=graph,
        universe=FakeUniverse({"fixture": ("NEAR", "FAR")}),
        settings=_settings(),
        sink=sink,
    ).bind()

    payload = bus.request(_request()).payload

    assert [candidate["ticker"] for candidate in payload["candidates"]] == ["FAR"]
    assert payload["filter_trace"]["dropped_by_filter"] == {"earnings_window": 1}
    assert payload["candidates"][0]["metrics"]["days_to_earnings"] == 30.0
    assert sink.faults == []
