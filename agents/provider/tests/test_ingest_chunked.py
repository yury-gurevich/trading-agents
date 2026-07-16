"""Chunked-ingest tests — paced sub-batches reassembled into one batch.

Agent: provider
Role: verify the universe is split into paced chunks, each chunk fetched and
      written as a MarketSnapshot part, the parts reassembled into one MarketData
      batch over the full universe, and that ingest_once dispatches to the chunked
      path when ingest_chunk_size is configured.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from agents.provider import ProviderAgent
from agents.provider.ingest import MARKET_FIELDS, _today_window, ingest_once
from agents.provider.ingest_chunked import (
    _chunks,
    _merge_parts,
    _optional_notes,
    ingest_chunked,
)
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from contracts.common import Window
from contracts.provider import (
    MARKET_DATA_LABEL,
    DataRequest,
    MarketData,
    OHLCVBar,
)
from kernel import InMemoryGraphStore, InProcessBus

_UNIVERSE = ("AAA", "BBB", "CCC", "DDD", "EEE")


def _bar(ticker: str, days_ago: int) -> OHLCVBar:
    # Recent dates so bars fall inside ingest's rolling _today_window().
    return OHLCVBar(
        ticker=ticker,
        bar_date=datetime.now(tz=UTC).date() - timedelta(days=days_ago),
        open=100.0,
        high=102.0,
        low=99.0,
        close=101.0,
        volume=1000,
    )


def _agent(
    graph: InMemoryGraphStore,
    *,
    chunk_size: int = 0,
    chunk_delay: float = 0.0,
) -> ProviderAgent:
    bars = tuple(_bar(t, d) for t in _UNIVERSE for d in (1, 2))
    source = FakeDataSource(
        bars=bars,
        fundamentals={t: {"pe": 10.0} for t in _UNIVERSE},
        news=dict.fromkeys(_UNIVERSE, ("headline",)),
        sectors=dict.fromkeys(_UNIVERSE, "Tech"),
        earnings={t: date(2026, 2, 1) for t in _UNIVERSE},
    )
    return ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=source,
        settings=ProviderSettings(
            ingest_chunk_size=chunk_size,
            ingest_chunk_delay_seconds=chunk_delay,
        ),
    )


def test_chunks_splits_into_consecutive_subbatches() -> None:
    assert _chunks(_UNIVERSE, 2) == (("AAA", "BBB"), ("CCC", "DDD"), ("EEE",))
    assert _chunks(_UNIVERSE, 99) == (_UNIVERSE,)
    assert _chunks(_UNIVERSE, 0) == tuple((t,) for t in _UNIVERSE)


def _part_with_notes(agent: ProviderAgent, notes: tuple[str, ...]) -> MarketData:
    base = agent._get_market_data(
        DataRequest(tickers=_UNIVERSE, window=_today_window(), fields=MARKET_FIELDS)
    )
    return base.model_copy(
        update={"quality": base.quality.model_copy(update={"notes": notes})}
    )


def test_optional_notes_keeps_only_degraded() -> None:
    agent = _agent(InMemoryGraphStore())
    part = _part_with_notes(
        agent,
        (
            "inconsistent_ohlcv_rejected",
            "news_degraded",
            "fundamentals_degraded:2:AAPL,MSFT:429",
        ),
    )
    assert _optional_notes((part,)) == (
        "news_degraded",
        "fundamentals_degraded:2:AAPL,MSFT:429",
    )


def test_merge_parts_revalidates_full_batch_dropping_per_chunk_ohlcv_notes() -> None:
    graph = InMemoryGraphStore()
    agent = _agent(graph)
    window = _today_window()
    # per-chunk quality carries an OHLCV-side note + a real optional fault
    part = _part_with_notes(
        agent, ("inconsistent_ohlcv_rejected", "news_degraded:1:AAPL:429")
    )
    merged = _merge_parts(agent, (part,), _UNIVERSE, window)
    # OHLCV recomputed on the full (clean) batch -> spurious per-chunk note gone
    assert "inconsistent_ohlcv_rejected" not in merged.quality.notes
    # the real optional-field fault is carried over as a NOTE, but no longer taints
    # the batch (DRIFT-012); the recomputed OHLCV is clean, so used_fallback is False
    assert "news_degraded:1:AAPL:429" in merged.quality.notes
    assert merged.quality.used_fallback is False


def test_ingest_chunked_paces_and_reassembles_one_batch() -> None:
    graph = InMemoryGraphStore()
    agent = _agent(graph)
    slept: list[float] = []

    key = ingest_chunked(
        agent,
        _UNIVERSE,
        "run-1",
        chunk_size=2,
        delay_seconds=7.0,
        sleep=slept.append,
    )

    # 3 chunks -> 2 inter-chunk pauses of the configured delay.
    assert slept == [7.0, 7.0]
    batch = graph.list_nodes(MARKET_DATA_LABEL)
    assert key == f"market-data:{batch[0].props['run_id']}"
    assert key == "market-data:run-1"
    # One reassembled MarketData batch over the full universe.
    assert len(batch) == 1
    assert sorted(batch[0].props["tickers"]) == sorted(_UNIVERSE)
    snapshot = batch[0].props["snapshot"]
    assert {b["ticker"] for b in snapshot["bars"]} == set(_UNIVERSE)
    assert set(snapshot["fundamentals"]) == set(_UNIVERSE)
    # 3 per-chunk parts + 1 reassembled batch snapshot.
    assert len(graph.list_nodes("MarketSnapshot")) == 4


def test_ingest_chunked_empty_universe_is_noop() -> None:
    graph = InMemoryGraphStore()
    assert (
        ingest_chunked(_agent(graph), (), "run-1", chunk_size=2, delay_seconds=1.0)
        is None
    )
    assert graph.list_nodes(MARKET_DATA_LABEL) == ()


def test_merge_parts_keeps_first_non_empty_benchmark() -> None:
    graph = InMemoryGraphStore()
    agent = _agent(graph)
    base = agent._get_market_data(
        DataRequest(
            tickers=("AAA",),
            window=Window(start=date(2026, 1, 1), end=date(2026, 1, 3)),
            fields=("ohlcv",),
        )
    )
    with_bench = base.model_copy(update={"benchmark": (_bar("SPY", 1),)})
    merged = _merge_parts(agent, (base, with_bench), _UNIVERSE, _today_window())
    assert merged.benchmark[0].ticker == "SPY"


def test_ingest_once_dispatches_to_chunked_when_configured() -> None:
    graph = InMemoryGraphStore()
    agent = _agent(graph, chunk_size=2, chunk_delay=0.0)
    key = ingest_once(agent, _UNIVERSE)
    assert key is not None
    # Chunked path wrote multiple MarketSnapshot parts (3 chunks) + 1 batch.
    assert len(graph.list_nodes("MarketSnapshot")) == 4


def test_ingest_once_single_shot_when_chunking_disabled() -> None:
    graph = InMemoryGraphStore()
    agent = _agent(graph, chunk_size=0)
    ingest_once(agent, _UNIVERSE)
    # Single-shot path: exactly one MarketSnapshot for the whole universe.
    assert len(graph.list_nodes("MarketSnapshot")) == 1
