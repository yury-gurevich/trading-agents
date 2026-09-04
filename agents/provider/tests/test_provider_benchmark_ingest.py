"""Provider benchmark-series ingest tests (S195).

Agent: provider
Role: verify the run's declared benchmark ticker reaches the persisted snapshot,
      so the scanner's beta cap has a denominator to gate on.
External I/O: none.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from agents.provider import ProviderAgent
from agents.provider.ingest_chunked import ingest_chunked
from agents.provider.poll import ingest_run_node
from agents.provider.sources import FakeDataSource
from contracts.provider import (
    MARKET_DATA_LABEL,
    RUN_REQUEST_BENCHMARK_TICKER_PROP,
    RUN_REQUEST_LABEL,
    RUN_REQUEST_LOOKBACK_DAYS_PROP,
    RUN_REQUEST_REQUIRED_HISTORY_BARS_PROP,
    MarketData,
    OHLCVBar,
)
from kernel import InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from pydantic import BaseModel

    from kernel import Node

_START = date(2026, 1, 2)


def _bars(ticker: str, closes: tuple[float, ...]) -> tuple[OHLCVBar, ...]:
    return tuple(
        OHLCVBar(
            ticker=ticker,
            bar_date=date.fromordinal(_START.toordinal() + offset),
            open=close,
            high=close,
            low=close,
            close=close,
            volume=1_000_000,
        )
        for offset, close in enumerate(closes)
    )


def _agent(graph: InMemoryGraphStore) -> ProviderAgent:
    source = FakeDataSource(
        bars=(
            *_bars("AAPL", (100.0, 101.0, 102.0)),
            *_bars("SPY", (400.0, 402.0, 404.0)),
        )
    )
    return ProviderAgent(InProcessBus(), graph=graph, source=source)


def _run_request(graph: InMemoryGraphStore, **extra: object) -> Node:
    return graph.merge_node(
        RUN_REQUEST_LABEL,
        "run-request:r1",
        {
            "run_id": "r1",
            "tickers": ["AAPL"],
            RUN_REQUEST_LOOKBACK_DAYS_PROP: 365,
            RUN_REQUEST_REQUIRED_HISTORY_BARS_PROP: 200,
            **extra,
        },
    )


def _snapshot(graph: InMemoryGraphStore) -> MarketData:
    node = graph.get_node(MARKET_DATA_LABEL, "market-data:r1")
    assert node is not None
    return MarketData.model_validate(node.props["snapshot"])


def test_declared_benchmark_reaches_the_persisted_snapshot() -> None:
    """The run names SPY; the snapshot the scanner pulls carries SPY's bars."""
    graph = InMemoryGraphStore()
    ingest_run_node(
        _run_request(graph, **{RUN_REQUEST_BENCHMARK_TICKER_PROP: "SPY"}),
        agent=_agent(graph),
    )
    benchmark = _snapshot(graph).benchmark
    assert {bar.ticker for bar in benchmark} == {"SPY"}
    assert len(benchmark) == 3


def test_no_declared_benchmark_leaves_the_series_empty() -> None:
    """A run that names no benchmark ingests none — the beta cap simply skips."""
    graph = InMemoryGraphStore()
    ingest_run_node(_run_request(graph), agent=_agent(graph))
    assert _snapshot(graph).benchmark == ()


def test_blank_benchmark_prop_is_treated_as_unnamed() -> None:
    graph = InMemoryGraphStore()
    ingest_run_node(
        _run_request(graph, **{RUN_REQUEST_BENCHMARK_TICKER_PROP: "   "}),
        agent=_agent(graph),
    )
    assert _snapshot(graph).benchmark == ()


def test_non_string_benchmark_prop_is_treated_as_unnamed() -> None:
    graph = InMemoryGraphStore()
    ingest_run_node(
        _run_request(graph, **{RUN_REQUEST_BENCHMARK_TICKER_PROP: 7}),
        agent=_agent(graph),
    )
    assert _snapshot(graph).benchmark == ()


def test_benchmark_prop_is_normalised_to_upper_case() -> None:
    graph = InMemoryGraphStore()
    ingest_run_node(
        _run_request(graph, **{RUN_REQUEST_BENCHMARK_TICKER_PROP: " spy "}),
        agent=_agent(graph),
    )
    assert {bar.ticker for bar in _snapshot(graph).benchmark} == {"SPY"}


def test_chunked_ingest_asks_for_the_benchmark_once() -> None:
    """One series serves the whole batch, so only the first chunk requests it."""
    graph = InMemoryGraphStore()
    source = FakeDataSource(
        bars=(
            *_bars("AAPL", (100.0, 101.0, 102.0)),
            *_bars("MSFT", (200.0, 202.0, 204.0)),
            *_bars("SPY", (400.0, 402.0, 404.0)),
        )
    )
    agent = ProviderAgent(InProcessBus(), graph=graph, source=source)
    asked: list[str | None] = []
    original = agent._get_market_data

    def _record(request: BaseModel) -> MarketData:
        asked.append(getattr(request, "benchmark_ticker", None))
        return original(request)

    agent._get_market_data = _record  # type: ignore[method-assign]
    key = ingest_chunked(
        agent,
        ("AAPL", "MSFT"),
        "r1",
        chunk_size=1,
        delay_seconds=0.0,
        lookback_days=365,
        benchmark_ticker="SPY",
        sleep=lambda _seconds: None,
    )
    assert key == "market-data:r1"
    assert asked == ["SPY", None]
    assert {bar.ticker for bar in _snapshot(graph).benchmark} == {"SPY"}
