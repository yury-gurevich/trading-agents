"""Scanner provider request helpers.

Agent: scanner
Role: send provider data requests over the injected message bus.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.provider import DataRequest, MarketData
from kernel import AgentMessage, FaultSink, MessageBus
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from contracts.common import Window
    from contracts.provider import OHLCVBar


def request_market_data(
    bus: MessageBus, sink: FaultSink, tickers: tuple[str, ...], window: Window
) -> MarketData | None:
    """Request OHLCV data from provider over the bus; ``None`` on any fault."""
    market: MarketData | None = None
    with fault_boundary(
        sink,
        agent="scanner",
        module="agents.scanner.provider_client",
        capability="run_scan",
        reraise=False,
    ) as capture:
        response = bus.request(
            AgentMessage(
                sender="scanner",
                recipient="provider",
                message_type="request",
                capability="get_market_data",
                payload=DataRequest(tickers=tickers, window=window).model_dump(
                    mode="json"
                ),
            )
        )
        if response.message_type == "error":
            message = str(response.payload.get("message", "provider error"))
            raise RuntimeError(message)
        market = MarketData.model_validate(response.payload)
    return None if capture.fault is not None else market


def request_benchmark_bars(
    bus: MessageBus, sink: FaultSink, benchmark_ticker: str, window: Window
) -> tuple[OHLCVBar, ...]:
    """Request benchmark OHLCV in isolation; return ``()`` on any fault.

    Kept separate from the candidate request so a missing/degraded benchmark never
    degrades candidate data quality — it only forgoes the beta-cap signal.
    """
    bars: tuple[OHLCVBar, ...] = ()
    with fault_boundary(
        sink,
        agent="scanner",
        module="agents.scanner.provider_client",
        capability="run_scan",
        reraise=False,
    ) as capture:
        response = bus.request(
            AgentMessage(
                sender="scanner",
                recipient="provider",
                message_type="request",
                capability="get_market_data",
                payload=DataRequest(
                    tickers=(benchmark_ticker,), window=window, fields=("ohlcv",)
                ).model_dump(mode="json"),
            )
        )
        bars = MarketData.model_validate(response.payload).bars
    return () if capture.fault is not None else bars
