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

from agents.provider.domain.integrity import validate_bars
from agents.provider.ingest import (
    MARKET_FIELDS,
    _today_window,
    _with_cached_sectors,
    _write_market_data,
    _write_regime_context,
)
from agents.provider.store import write_market_snapshot
from contracts.provider import DataRequest, MarketData, RegimeRequest

if TYPE_CHECKING:
    from collections.abc import Callable

    from agents.provider.agent import ProviderAgent
    from contracts.common import Window


def _chunks(universe: tuple[str, ...], size: int) -> tuple[tuple[str, ...], ...]:
    """Split *universe* into consecutive sub-batches of at most *size* tickers."""
    step = max(1, size)
    return tuple(universe[i : i + step] for i in range(0, len(universe), step))


def _optional_notes(parts: tuple[MarketData, ...]) -> tuple[str, ...]:
    """Per-chunk optional-field fault notes (`*_degraded`) — kept across the merge.

    These are real fetch faults. OHLCV-side notes are NOT kept here: they are recomputed
    on the full batch (per-chunk validation saw only partial data — DL-17).
    """
    return tuple(
        dict.fromkeys(
            note
            for part in parts
            for note in part.quality.notes
            if note.endswith("_degraded")
        )
    )


def _merge_parts(
    agent: ProviderAgent,
    parts: tuple[MarketData, ...],
    universe: tuple[str, ...],
    window: Window,
) -> MarketData:
    """Reassemble parts into one batch, validating OHLCV quality on the FULL universe.

    Per-chunk validation (DL-17) computed sigma/staleness on partial data, re-tripping
    them spuriously; here OHLCV quality is recomputed once over the reassembled batch,
    and only the real per-chunk optional-field faults (`*_degraded`) are carried over.
    """
    bars = tuple(chain.from_iterable(p.bars for p in parts))
    validated, ohlcv = validate_bars(universe, bars, window, agent._settings)
    optional = _optional_notes(parts)
    quality = ohlcv.model_copy(
        update={
            # Optional-field faults are recorded as notes but do NOT taint
            # used_fallback (DRIFT-012); only core OHLCV degradation blocks.
            "used_fallback": ohlcv.used_fallback,
            "notes": tuple(dict.fromkeys((*ohlcv.notes, *optional))),
        }
    )
    provenance = write_market_snapshot(
        agent._graph, tickers=universe, bars=validated, quality=quality
    )
    return MarketData(
        bars=validated,
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
    run_id: str,
    *,
    chunk_size: int,
    delay_seconds: float,
    fields: tuple[str, ...] = MARKET_FIELDS,
    sleep: Callable[[float], None] = time.sleep,
) -> str | None:
    """Fetch *universe* in paced chunks, reassemble one batch, write it once.

    Each chunk is fetched through ``agent._get_market_data`` (its own fault
    boundary + MarketSnapshot part); ``sleep(delay_seconds)`` paces the gap
    between chunks so the aggregate per-minute API call rate stays under the
    free-tier ceiling. The reassembled node is keyed by *run_id* (DRIFT-011).
    Returns the reassembled MarketData node key, or ``None`` when *universe* is empty.
    """
    if not universe:
        return None
    window = _today_window()
    chunks = _chunks(universe, chunk_size)
    parts: list[MarketData] = []
    for index, chunk in enumerate(chunks):
        parts.append(
            agent._get_market_data(
                DataRequest(tickers=chunk, window=window, fields=fields)
            )
        )
        if index < len(chunks) - 1:
            sleep(delay_seconds)
    market = _merge_parts(agent, tuple(parts), universe, window)
    market = _with_cached_sectors(agent._graph, market, universe)
    _write_market_data(agent._graph, market, universe, window, run_id)
    regime = agent._get_regime(RegimeRequest(as_of=window.end))
    _write_regime_context(agent._graph, regime, window, run_id)
    return f"market-data:{run_id}"
