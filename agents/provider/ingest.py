"""Provider standalone ingest loop — graph-as-queue pull model.

Agent: provider
Role: proactively fetch all market data for the configured universe and write
      it to the graph so downstream agents can poll for new work.
External I/O: none directly (delegates to ProviderAgent which calls DataSource).
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from contracts.common import Window
from contracts.provider import (
    MARKET_DATA_LABEL,
    REGIME_CONTEXT_LABEL,
    DataRequest,
    RegimeRequest,
)

if TYPE_CHECKING:
    from agents.provider.agent import ProviderAgent
    from contracts.provider import MarketData, RegimeContext
    from kernel import GraphStore

_DEFAULT_LOOKBACK_DAYS = 60
MARKET_FIELDS = ("ohlcv", "news", "fundamentals", "sectors", "earnings_calendar")


def universe_from_env() -> tuple[str, ...]:
    """Parse PROVIDER_UNIVERSE env var into a tuple of tickers.

    Expects a comma-separated list (e.g. ``AAPL,MSFT,TSLA``).
    Returns an empty tuple when the variable is unset or blank.
    """
    raw = os.environ.get("PROVIDER_UNIVERSE", "")
    return tuple(t.strip().upper() for t in raw.split(",") if t.strip())


def _today_window(lookback_days: int = _DEFAULT_LOOKBACK_DAYS) -> Window:
    """Return a Window from (today - lookback_days) to today."""
    today = datetime.now(tz=UTC).date()
    return Window(start=today - timedelta(days=lookback_days), end=today)


def _write_market_data(
    graph: GraphStore,
    market: MarketData,
    universe: tuple[str, ...],
    window: Window,
    run_id: str,
) -> None:
    """Persist the full market payload so downstream agents read it from the graph.

    Keyed by **run_id** (DRIFT-011): each run's facts are an immutable, independent
    node, so a same-day re-run does not collide on the append-only ``snapshot`` (the
    in-memory store hid this; Neo4j enforces immutability). Downstream finds it by the
    ``INGESTED_BY`` / ``DERIVED_FROM`` edge, and links the regime via ``run_id``.
    """
    graph.merge_node(
        MARKET_DATA_LABEL,
        f"market-data:{run_id}",
        {
            "snapshot": market.model_dump(mode="json"),
            "tickers": list(universe),
            "window_end": window.end.isoformat(),
            "run_id": run_id,
        },
    )


def _write_regime_context(
    graph: GraphStore, regime: RegimeContext, window: Window, run_id: str
) -> None:
    """Persist the full regime payload so downstream agents read it from the graph.

    Keyed by **run_id** (DRIFT-011) to match the MarketData of the same run; the
    analyst/PM derive this key from ``market_node.props['run_id']``.
    """
    graph.merge_node(
        REGIME_CONTEXT_LABEL,
        f"regime-context:{run_id}",
        {
            "snapshot": regime.model_dump(mode="json"),
            "window_end": window.end.isoformat(),
            "run_id": run_id,
        },
    )


def ingest_once(
    agent: ProviderAgent, universe: tuple[str, ...], run_id: str | None = None
) -> str | None:
    """Fetch all data fields for *universe*, write them to the graph, return the key.

    Calls get_market_data (OHLCV + news + fundamentals + sectors + earnings) and
    get_regime so the graph reflects the current market state, and persists the
    full ``MarketData`` + ``RegimeContext`` payloads for downstream graph-pull
    agents, keyed by *run_id* (DRIFT-011). Returns the ``MarketData`` node key
    written, or ``None`` (no-op) when *universe* is empty. A missing *run_id*
    defaults to a fresh uuid so a standalone ingest is still collision-free.
    """
    if not universe:
        return None
    key_id = run_id or uuid.uuid4().hex
    chunk_size = getattr(agent._settings, "ingest_chunk_size", 0)
    if chunk_size and chunk_size > 0 and len(universe) > chunk_size:
        from agents.provider.ingest_chunked import ingest_chunked

        return ingest_chunked(
            agent,
            universe,
            key_id,
            chunk_size=chunk_size,
            delay_seconds=agent._settings.ingest_chunk_delay_seconds,
        )
    window = _today_window()
    market_request = DataRequest(
        tickers=universe,
        window=window,
        fields=MARKET_FIELDS,
    )
    market = agent._get_market_data(market_request)
    _write_market_data(agent._graph, market, universe, window, key_id)
    regime = agent._get_regime(RegimeRequest(as_of=window.end))
    _write_regime_context(agent._graph, regime, window, key_id)
    return f"market-data:{key_id}"
