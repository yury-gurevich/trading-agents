"""Provider chunked ingest — paced sub-batches reassembled into one batch.

Agent: provider
Role: split the universe into chunk_size sub-batches, fetch each behind the
      provider's normal fault boundary with a delay between chunks (to stay under
      free-tier per-minute API limits — Finnhub is per-ticker, ~60 calls/min),
      then reassemble ONE MarketData batch and write it as a single downstream
      work item. The reassembled batch is the training-relevant unit (DL-17);
      each chunk still writes its own MarketSnapshot "part".
External I/O: none directly (delegates to ProviderAgent / DataSource); paces via sleep.
"""

from __future__ import annotations

import time
from itertools import chain
from typing import TYPE_CHECKING

from agents.provider.ingest import (
    MARKET_FIELDS,
    _today_window,
    _write_market_data,
    _write_regime_context,
)
from agents.provider.store import write_market_snapshot
from contracts.provider import DataQualityTrace, DataRequest, MarketData, RegimeRequest

if TYPE_CHECKING:
    from collections.abc import Callable

    from agents.provider.agent import ProviderAgent


def _chunks(universe: tuple[str, ...], size: int) -> tuple[tuple[str, ...], ...]:
    """Split *universe* into consecutive sub-batches of at most *size* tickers."""
    step = max(1, size)
    return tuple(universe[i : i + step] for i in range(0, len(universe), step))


def _combine_quality(traces: tuple[DataQualityTrace, ...]) -> DataQualityTrace:
    """Fold per-chunk quality traces into one honest batch-level trace."""
    return DataQualityTrace(
        requested=sum(t.requested for t in traces),
        returned=sum(t.returned for t in traces),
        used_fallback=any(t.used_fallback for t in traces),
        stale_tickers=tuple(sorted({s for t in traces for s in t.stale_tickers})),
        notes=tuple(dict.fromkeys(n for t in traces for n in t.notes)),
    )


def _merge_parts(
    agent: ProviderAgent,
    parts: tuple[MarketData, ...],
    universe: tuple[str, ...],
) -> MarketData:
    """Reassemble per-chunk MarketData parts into one batch over the full universe."""
    bars = tuple(chain.from_iterable(p.bars for p in parts))
    quality = _combine_quality(tuple(p.quality for p in parts))
    provenance = write_market_snapshot(
        agent._graph, tickers=universe, bars=bars, quality=quality
    )
    return MarketData(
        bars=bars,
        benchmark=next((p.benchmark for p in parts if p.benchmark), ()),
        fundamentals={k: v for p in parts for k, v in p.fundamentals.items()},
        news={k: v for p in parts for k, v in p.news.items()},
        sentiment={k: v for p in parts for k, v in p.sentiment.items()},
        sectors={k: v for p in parts for k, v in p.sectors.items()},
        earnings={k: v for p in parts for k, v in p.earnings.items()},
        quality=quality,
        provenance=provenance,
    )


def ingest_chunked(
    agent: ProviderAgent,
    universe: tuple[str, ...],
    *,
    chunk_size: int,
    delay_seconds: float,
    sleep: Callable[[float], None] = time.sleep,
) -> str | None:
    """Fetch *universe* in paced chunks, reassemble one batch, write it once.

    Each chunk is fetched through ``agent._get_market_data`` (its own fault
    boundary + MarketSnapshot part); ``sleep(delay_seconds)`` paces the gap
    between chunks so the aggregate per-minute API call rate stays under the
    free-tier ceiling. Returns the reassembled MarketData node key, or ``None``
    when *universe* is empty.
    """
    if not universe:
        return None
    window = _today_window()
    chunks = _chunks(universe, chunk_size)
    parts: list[MarketData] = []
    for index, chunk in enumerate(chunks):
        parts.append(
            agent._get_market_data(
                DataRequest(tickers=chunk, window=window, fields=MARKET_FIELDS)
            )
        )
        if index < len(chunks) - 1:
            sleep(delay_seconds)
    market = _merge_parts(agent, tuple(parts), universe)
    _write_market_data(agent._graph, market, universe, window)
    regime = agent._get_regime(RegimeRequest(as_of=window.end))
    _write_regime_context(agent._graph, regime, window)
    return f"market-data:{window.end.isoformat()}"
