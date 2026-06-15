"""Provider agent implementation.

Agent: provider
Role: answer provider contract capabilities over the in-process message bus.
External I/O: injected DataSource and GraphStore backends.
"""

from __future__ import annotations

from datetime import UTC, datetime, time
from typing import TYPE_CHECKING

from agents.provider.domain.integrity import degraded_quality, validate_bars
from agents.provider.domain.regime import classify_regime
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
from kernel import AgentBase, CollectingFaultSink, FaultSink, GraphStore, MessageBus
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
        fundamentals: dict[str, dict[str, float]] = {}
        if "fundamentals" in data_request.fields:
            with fault_boundary(
                self.sink,
                agent="provider",
                module="agents.provider.agent",
                capability="get_market_data",
                reraise=False,
            ) as fcapture:
                fundamentals = self._source.fetch_fundamentals(
                    data_request.tickers, data_request.window
                )
            if fcapture.fault is not None:
                fundamentals = {}
                quality = quality.model_copy(
                    update={
                        "notes": (*quality.notes, "fundamentals_degraded"),
                        "used_fallback": True,
                    }
                )
        news: dict[str, tuple[str, ...]] = {}
        if "news" in data_request.fields:
            with fault_boundary(
                self.sink,
                agent="provider",
                module="agents.provider.agent",
                capability="get_market_data",
                reraise=False,
            ) as ncapture:
                news = self._source.fetch_news(
                    data_request.tickers, data_request.window
                )
            if ncapture.fault is not None:
                news = {}
                quality = quality.model_copy(
                    update={
                        "notes": (*quality.notes, "news_degraded"),
                        "used_fallback": True,
                    }
                )
        provenance = write_market_snapshot(
            self._graph,
            tickers=data_request.tickers,
            bars=bars,
            quality=quality,
        )
        return MarketData(
            bars=bars,
            fundamentals=fundamentals,
            news=news,
            quality=quality,
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
