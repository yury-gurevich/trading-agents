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
from contracts.provider import DataRequest, RegimeRequest

if TYPE_CHECKING:
    from agents.provider.agent import ProviderAgent

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


def ingest_once(agent: ProviderAgent, universe: tuple[str, ...]) -> None:
    """Fetch all data fields for *universe* and write the results to the graph.

    Calls both get_market_data (OHLCV + news + fundamentals + sectors +
    earnings) and get_regime so the graph reflects the current market state.
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
    agent._get_market_data(market_request)
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
