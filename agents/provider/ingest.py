"""Provider standalone ingest loop — graph-as-queue pull model.

Agent: provider
Role: proactively fetch all market data for the configured universe and write
      it to the graph so downstream agents can poll for new work.
External I/O: none directly (delegates to ProviderAgent which calls DataSource).
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from contracts.common import Window
from contracts.provider import MARKET_DATA_LABEL, DataRequest, RegimeRequest

if TYPE_CHECKING:
    from agents.provider.agent import ProviderAgent
    from contracts.provider import MarketData
    from kernel import GraphStore

_DEFAULT_LOOKBACK_DAYS = 60
_DEFAULT_POLL_INTERVAL = 3600


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
) -> None:
    """Persist the full market payload so downstream agents read it from the graph.

    Keyed by window-end date so a re-run on the same day idempotently updates the
    node and a new day creates fresh, pickable work (DL-08b).
    """
    graph.merge_node(
        MARKET_DATA_LABEL,
        f"market-data:{window.end.isoformat()}",
        {
            "snapshot": market.model_dump(mode="json"),
            "tickers": list(universe),
            "window_end": window.end.isoformat(),
        },
    )


def ingest_once(agent: ProviderAgent, universe: tuple[str, ...]) -> None:
    """Fetch all data fields for *universe* and write the results to the graph.

    Calls get_market_data (OHLCV + news + fundamentals + sectors + earnings) and
    get_regime so the graph reflects the current market state, and persists the
    full market payload as a ``MarketData`` node for downstream graph-pull agents.
    A no-op when *universe* is empty.
    """
    if not universe:
        return
    window = _today_window()
    market_request = DataRequest(
        tickers=universe,
        window=window,
        fields=("ohlcv", "news", "fundamentals", "sectors", "earnings_calendar"),
    )
    market = agent._get_market_data(market_request)
    _write_market_data(agent._graph, market, universe, window)
    regime_request = RegimeRequest(as_of=window.end)
    agent._get_regime(regime_request)


def ingest_loop(  # pragma: no cover
    agent: ProviderAgent,
    universe: tuple[str, ...],
) -> None:
    """Proactively ingest on a schedule. Blocks forever.

    Poll interval is read from PROVIDER_POLL_INTERVAL (seconds); default 3600.
    """
    import time

    interval = int(
        os.environ.get("PROVIDER_POLL_INTERVAL", str(_DEFAULT_POLL_INTERVAL))
    )
    while True:
        ingest_once(agent, universe)
        time.sleep(interval)
