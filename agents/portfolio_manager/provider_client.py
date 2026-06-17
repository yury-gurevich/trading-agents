"""Portfolio Manager provider request helpers.

Agent: portfolio_manager
Role: send provider requests over the injected message bus.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from contracts.common import Money
from contracts.provider import (
    DataRequest,
    MarketData,
    OHLCVBar,
    RegimeContext,
    RegimeRequest,
)
from kernel import AgentMessage, FaultSink, MessageBus
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from datetime import date

    from contracts.analyst import RecommendationSet
    from contracts.common import Window


def request_market_data(
    bus: MessageBus,
    sink: FaultSink,
    recommendation_set: RecommendationSet,
    window: Window,
) -> MarketData | None:
    """Request recommendation ticker OHLCV data from provider over the bus."""
    market: MarketData | None = None
    with fault_boundary(
        sink,
        agent="portfolio_manager",
        module="agents.portfolio_manager.provider_client",
        capability="evaluate_orders",
        reraise=False,
    ) as capture:
        response = bus.request(
            AgentMessage(
                sender="portfolio_manager",
                recipient="provider",
                message_type="request",
                capability="get_market_data",
                payload=DataRequest(
                    tickers=tuple(
                        item.ticker for item in recommendation_set.recommendations
                    ),
                    window=window,
                    fields=("ohlcv", "sectors"),
                ).model_dump(mode="json"),
            )
        )
        if response.message_type == "error":
            message = str(response.payload.get("message", "provider error"))
            raise RuntimeError(message)
        market = MarketData.model_validate(response.payload)
    return None if capture.fault is not None else market


def request_regime(
    bus: MessageBus, sink: FaultSink, as_of: date
) -> RegimeContext | None:
    """Request current regime policy from provider over the bus."""
    regime: RegimeContext | None = None
    with fault_boundary(
        sink,
        agent="portfolio_manager",
        module="agents.portfolio_manager.provider_client",
        capability="evaluate_orders",
        reraise=False,
    ) as capture:
        response = bus.request(
            AgentMessage(
                sender="portfolio_manager",
                recipient="provider",
                message_type="request",
                capability="get_regime",
                payload=RegimeRequest(as_of=as_of).model_dump(mode="json"),
            )
        )
        if response.message_type == "error":
            message = str(response.payload.get("message", "provider error"))
            raise RuntimeError(message)
        regime = RegimeContext.model_validate(response.payload)
    return None if capture.fault is not None else regime


def latest_close_prices(market: MarketData) -> dict[str, Money]:
    """Return each ticker's latest close as a Decimal-backed Money value."""
    latest: dict[str, OHLCVBar] = {}
    for bar in market.bars:
        current = latest.get(bar.ticker)
        if current is None or bar.bar_date > current.bar_date:
            latest[bar.ticker] = bar
    return {
        ticker: Money(amount=Decimal(str(bar.close))) for ticker, bar in latest.items()
    }
