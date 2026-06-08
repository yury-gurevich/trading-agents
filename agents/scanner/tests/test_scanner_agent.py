"""ScannerAgent bus, filter, and provenance tests.

Agent: scanner
Role: verify scanner-to-provider calls over the in-process bus.
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


def _request(capability: str = "run_scan") -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="scanner",
        message_type="request",
        capability=capability,
        payload={"run_id": "scan-test", "universe": "fixture"},
    )


def _wire(
    *,
    bars: tuple[OHLCVBar, ...],
    fail_provider: bool = False,
    register_provider: bool = True,
    settings: ScannerSettings | None = None,
) -> tuple[InProcessBus, InMemoryGraphStore, CollectingFaultSink]:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    scanner_sink = CollectingFaultSink()
    if register_provider:
        ProviderAgent(
            bus,
            graph=graph,
            source=FakeDataSource(bars=bars, fail_ohlcv=fail_provider),
        ).bind()
    ScannerAgent(
        bus,
        graph=graph,
        universe=FakeUniverse(
            {"fixture": ("AAPL", "MSFT", "PENNY", "THIN", "MISSING")}
        ),
        settings=settings
        or ScannerSettings(
            min_relative_strength=0.02,
            min_price=5.0,
            min_average_volume=500_000.0,
            candidate_cap=2,
            lookback_days=7,
        ),
        sink=scanner_sink,
    ).bind()
    return bus, graph, scanner_sink


def _fixture_bars() -> tuple[OHLCVBar, ...]:
    return (
        _bar("AAPL", 5, 100.0, 1_000_000),
        _bar("AAPL", 0, 110.0, 1_200_000),
        _bar("MSFT", 5, 100.0, 1_000_000),
        _bar("MSFT", 0, 101.0, 1_100_000),
        _bar("PENNY", 5, 4.0, 1_000_000),
        _bar("PENNY", 0, 4.5, 1_000_000),
        _bar("THIN", 5, 50.0, 10_000),
        _bar("THIN", 0, 60.0, 20_000),
        _bar("MISSING", 0, 20.0, 1_000_000),
    )


def test_run_scan_calls_provider_and_returns_ranked_candidates() -> None:
    bus, _graph, scanner_sink = _wire(bars=_fixture_bars())

    response = bus.request(_request())

    payload = response.payload
    assert response.message_type == "response"
    assert [candidate["ticker"] for candidate in payload["candidates"]] == ["AAPL"]
    assert payload["candidates"][0]["rank"] == 1
    assert "min_relative_strength" in payload["candidates"][0]["survived_filters"]
    assert payload["filter_trace"]["universe_size"] == 5
    assert payload["filter_trace"]["evaluated"] == 5
    assert payload["filter_trace"]["dropped_by_filter"] == {
        "min_relative_strength": 1,
        "min_price": 1,
        "min_average_volume": 1,
        "missing_history": 1,
    }
    assert payload["explanation"]["summary"]
    assert payload["provenance"]["graph_node_id"].startswith("ScanRun:")
    assert scanner_sink.faults == []


def test_scan_provenance_links_candidates_to_provider_snapshot() -> None:
    bus, graph, _scanner_sink = _wire(bars=_fixture_bars())

    response = bus.request(_request())

    scan_key = response.payload["provenance"]["graph_node_id"].split(":", 1)[1]
    scan_node = graph.get_node("ScanRun", scan_key)
    assert scan_node is not None
    assert [node.label for node in graph.ancestors(scan_node, max_depth=1)] == [
        "Candidate"
    ]
    assert [
        node.label
        for node in graph.descendants(
            scan_node, max_depth=1, edge_types={"DERIVED_FROM"}
        )
    ] == ["MarketSnapshot"]


def test_degraded_provider_path_returns_empty_explained_result() -> None:
    bus, _graph, scanner_sink = _wire(bars=(), fail_provider=True)

    response = bus.request(_request())

    assert response.message_type == "response"
    assert response.payload["candidates"] == []
    assert response.payload["filter_trace"]["evaluated"] == 0
    assert response.payload["filter_trace"]["dropped_by_filter"] == {
        "provider_degraded": 5
    }
    assert "provider market data" in response.payload["explanation"]["summary"]
    assert len(scanner_sink.faults) == 1
    assert scanner_sink.faults[0].source_module == "agents.scanner.agent"


def test_provider_bus_error_returns_empty_explained_result() -> None:
    bus, _graph, scanner_sink = _wire(bars=(), register_provider=False)

    response = bus.request(_request())

    assert response.message_type == "response"
    assert response.payload["candidates"] == []
    assert response.payload["filter_trace"]["dropped_by_filter"] == {
        "provider_degraded": 5
    }
    assert scanner_sink.faults[0].error_type == "RuntimeError"


def test_clean_provider_with_no_survivors_explains_filter_result() -> None:
    bus, _graph, scanner_sink = _wire(
        bars=_fixture_bars(),
        settings=ScannerSettings(
            min_relative_strength=0.50,
            min_price=5.0,
            min_average_volume=500_000.0,
            candidate_cap=2,
            lookback_days=7,
        ),
    )

    response = bus.request(_request())

    assert response.message_type == "response"
    assert response.payload["candidates"] == []
    assert "No candidates survived" in response.payload["explanation"]["summary"]
    assert scanner_sink.faults == []


def test_explain_filter_returns_grounded_explanation() -> None:
    bus, _graph, _scanner_sink = _wire(bars=_fixture_bars())

    response = bus.request(_request("explain_filter"))

    assert response.message_type == "response"
    assert "relative strength" in response.payload["summary"]
    assert response.payload["evidence_refs"] == ["scanner.filters.core"]
