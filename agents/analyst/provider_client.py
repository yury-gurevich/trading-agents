"""Analyst provider request helpers.

Agent: analyst
Role: send provider requests over the injected message bus.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.provider import DataRequest, MarketData, RegimeContext, RegimeRequest
from kernel import AgentMessage, FaultSink, MessageBus
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from datetime import date

    from contracts.common import Window
    from contracts.scanner import CandidateSet


def request_market_data(
    bus: MessageBus,
    sink: FaultSink,
    candidate_set: CandidateSet,
    window: Window,
) -> MarketData | None:
    """Request candidate OHLCV data from provider over the bus."""
    market: MarketData | None = None
    with fault_boundary(
        sink,
        agent="analyst",
        module="agents.analyst.provider_client",
        capability="analyze",
        reraise=False,
    ) as capture:
        response = bus.request(
            AgentMessage(
                sender="analyst",
                recipient="provider",
                message_type="request",
                capability="get_market_data",
                payload=DataRequest(
                    tickers=tuple(
                        candidate.ticker for candidate in candidate_set.candidates
                    ),
                    window=window,
                    fields=("ohlcv", "fundamentals"),
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
    """Request market regime from provider over the bus."""
    regime: RegimeContext | None = None
    with fault_boundary(
        sink,
        agent="analyst",
        module="agents.analyst.provider_client",
        capability="analyze",
        reraise=False,
    ) as capture:
        response = bus.request(
            AgentMessage(
                sender="analyst",
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
