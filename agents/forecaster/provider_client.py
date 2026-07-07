"""Forecaster provider request helper.

Agent: forecaster
Role: request a subject's recent headlines from the provider over the bus.
External I/O: none (the bus carries the request; provider owns the market I/O).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.provider import DataRequest, MarketData
from kernel import AgentMessage, FaultSink, MessageBus
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from contracts.common import Window
    from contracts.provider import OHLCVBar


def request_news(
    bus: MessageBus, sink: FaultSink, ticker: str, window: Window
) -> dict[str, tuple[str, ...]]:
    """Request a ticker's recent headlines from provider; ``{}`` on any fault."""
    news: dict[str, tuple[str, ...]] = {}
    with fault_boundary(
        sink,
        agent="forecaster",
        module="agents.forecaster.provider_client",
        capability="forecast",
        reraise=False,
    ) as capture:
        response = bus.request(
            AgentMessage(
                sender="forecaster",
                recipient="provider",
                message_type="request",
                capability="get_market_data",
                payload=DataRequest(
                    tickers=(ticker,), window=window, fields=("news",)
                ).model_dump(mode="json"),
            )
        )
        if response.message_type == "error":
            message = str(response.payload.get("message", "provider error"))
            raise RuntimeError(message)
        news = dict(MarketData.model_validate(response.payload).news)
    return {} if capture.fault is not None else news


def request_prices(
    bus: MessageBus,
    sink: FaultSink,
    ticker: str,
    window: Window,
    *,
    capability: str = "forecast_return",
) -> tuple[OHLCVBar, ...]:
    """Request a ticker's recent OHLCV bars from provider; ``()`` on any fault."""
    bars: tuple[OHLCVBar, ...] = ()
    with fault_boundary(
        sink,
        agent="forecaster",
        module="agents.forecaster.provider_client",
        capability=capability,
        reraise=False,
    ) as capture:
        response = bus.request(
            AgentMessage(
                sender="forecaster",
                recipient="provider",
                message_type="request",
                capability="get_market_data",
                payload=DataRequest(
                    tickers=(ticker,), window=window, fields=("ohlcv",)
                ).model_dump(mode="json"),
            )
        )
        if response.message_type == "error":
            message = str(response.payload.get("message", "provider error"))
            raise RuntimeError(message)
        market = MarketData.model_validate(response.payload)
        bars = tuple(
            sorted(
                (bar for bar in market.bars if bar.ticker == ticker),
                key=lambda bar: bar.bar_date,
            )
        )
    return () if capture.fault is not None else bars
