"""Monitor provider request helpers.

Agent: monitor
Role: request current prices from provider over the injected message bus.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from contracts.common import Window
from contracts.provider import DataRequest, MarketData
from kernel import AgentMessage, FaultSink, MessageBus
from kernel.errors import fault_boundary

CENTS_PER_DOLLAR = Decimal("100")


def latest_close_cents(
    bus: MessageBus,
    sink: FaultSink,
    *,
    tickers: tuple[str, ...],
    lookback_days: int,
) -> dict[str, int] | None:
    """Request latest close prices and return integer cents by ticker."""
    if not tickers:
        return {}
    market: MarketData | None = None
    with fault_boundary(
        sink,
        agent="monitor",
        module="agents.monitor.provider_client",
        capability="check_positions",
        reraise=False,
    ) as capture:
        response = bus.request(
            AgentMessage(
                sender="monitor",
                recipient="provider",
                message_type="request",
                capability="get_market_data",
                payload=DataRequest(
                    tickers=tickers,
                    window=_window(lookback_days),
                ).model_dump(mode="json"),
            )
        )
        if response.message_type == "error":
            message = str(response.payload.get("message", "provider error"))
            raise RuntimeError(message)
        market = MarketData.model_validate(response.payload)
        if market.quality.used_fallback:
            raise RuntimeError("provider returned degraded market data")
    if capture.fault is not None or market is None:
        return None
    return _latest_cents(market)


def _window(lookback_days: int) -> Window:
    end = datetime.now(tz=UTC).date()
    return Window(start=end - timedelta(days=lookback_days), end=end)


def _latest_cents(market: MarketData) -> dict[str, int]:
    latest: dict[str, tuple[date, float]] = {}
    for bar in market.bars:
        current = latest.get(bar.ticker)
        if current is None or bar.bar_date > current[0]:
            latest[bar.ticker] = (bar.bar_date, bar.close)
    return {
        ticker: int(
            (Decimal(str(close)) * CENTS_PER_DOLLAR).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
        )
        for ticker, (_date, close) in latest.items()
    }
