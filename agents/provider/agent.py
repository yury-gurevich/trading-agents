"""Provider agent implementation.

Agent: provider
Role: answer provider contract capabilities over the in-process message bus and
      publish claim-check ready events on the pub/sub plane (P14 dual-mode).
External I/O: injected DataSource and GraphStore backends.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, time
from typing import TYPE_CHECKING, Any

from agents.provider.domain.integrity import degraded_quality, validate_bars
from agents.provider.domain.regime import classify_regime
from agents.provider.market_fields import collect_optional_fields
from agents.provider.settings import ProviderSettings
from agents.provider.sources import RegimeInputs
from agents.provider.store import write_market_snapshot, write_regime
from contracts.provider import (
    CONTRACT,
    DataRequest,
    MarketData,
    OHLCVBar,
    RegimeContext,
    RegimeRequest,
)
from kernel import AgentBase, CollectingFaultSink, FaultSink, GraphStore, MessageBus, claim_check_write
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from pydantic import BaseModel

    from agents.provider.sources import DataSource


class ProviderAgent(AgentBase):
    """Provider boundary agent."""

    def __init__(
        self,
        bus: MessageBus,
        *,
        graph: GraphStore,
        source: DataSource,
        settings: ProviderSettings | None = None,
        sink: FaultSink | None = None,
    ) -> None:
        """Create a provider agent with injected graph, source, settings, and sink."""
        super().__init__(CONTRACT, bus)
        self._graph = graph
        self._source = source
        self._settings = settings or ProviderSettings()
        self.sink = sink if sink is not None else CollectingFaultSink()
        self.handlers = {
            "get_market_data": self._get_market_data,
            "get_regime": self._get_regime,
        }

    def bind(self) -> None:
        """Register RPC handlers and subscribe to pub/sub data-request topic."""
        super().bind()
        self.bus.subscribe("data.request.market", self._on_market_data_request)

    def _on_market_data_request(self, event: dict[str, Any]) -> None:
        run_id: str | None = event.get("run_id")
        req = DataRequest.model_validate(event)
        market_data = self._get_market_data(req)
        claim_check_write(
            self.bus, self._graph,
            topic="data.ready.market",
            label="MarketDataEvent",
            ref=f"market-data:{run_id or uuid.uuid4().hex}",
            props={"snapshot": market_data.model_dump(mode="json")},
            run_id=run_id,
        )

    def _get_market_data(self, request: BaseModel) -> MarketData:
        data_request = DataRequest.model_validate(request)
        bars: tuple[OHLCVBar, ...] = ()
        with fault_boundary(
            self.sink,
            agent="provider",
            module="agents.provider.agent",
            capability="get_market_data",
            reraise=False,
        ) as capture:
            bars = self._source.fetch_ohlcv(data_request.tickers, data_request.window)
        if capture.fault is None:
            bars, quality = validate_bars(
                data_request.tickers, bars, data_request.window, self._settings
            )
        else:
            quality = degraded_quality(data_request.tickers, note="source_unavailable")
        optional = collect_optional_fields(
            self._source,
            fields=data_request.fields,
            tickers=data_request.tickers,
            window=data_request.window,
            sink=self.sink,
            quality=quality,
        )
        provenance = write_market_snapshot(
            self._graph,
            tickers=data_request.tickers,
            bars=bars,
            quality=optional.quality,
        )
        return MarketData(
            bars=bars,
            fundamentals=optional.fundamentals,
            news=optional.news,
            sentiment=optional.sentiment,
            sectors=optional.sectors,
            earnings=optional.earnings,
            quality=optional.quality,
            provenance=provenance,
        )

    def _get_regime(self, request: BaseModel) -> RegimeContext:
        regime_request = RegimeRequest.model_validate(request)
        inputs = RegimeInputs(as_of=regime_request.as_of)
        with fault_boundary(
            self.sink,
            agent="provider",
            module="agents.provider.agent",
            capability="get_regime",
            reraise=False,
        ) as capture:
            inputs = self._source.fetch_regime_inputs(regime_request.as_of)
        label = classify_regime(inputs, self._settings)
        as_of = datetime.combine(inputs.as_of, time.min, tzinfo=UTC)
        incident_refs = ("regime_source_degraded",) if capture.fault is not None else ()
        provenance = write_regime(
            self._graph,
            label=label,
            vix=inputs.vix,
            as_of=as_of,
            incident_refs=incident_refs,
        )
        return RegimeContext(
            label=label,
            vix=inputs.vix,
            as_of=as_of,
            base_min_confidence=self._settings.base_min_confidence,
            base_stop_loss_pct=self._settings.base_stop_loss_pct,
            base_take_profit_pct=self._settings.base_take_profit_pct,
            base_max_holding_days=self._settings.base_max_holding_days,
            provenance=provenance,
        )
