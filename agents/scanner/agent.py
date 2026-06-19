"""Scanner agent implementation.

Agent: scanner
Role: request provider market data over the bus, return ranked candidates via RPC,
      and publish scan.candidates.ready claim-check events on run.trigger.
External I/O: none.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from agents.scanner.domain.filters import apply_filters
from agents.scanner.domain.ranking import rank_survivors
from agents.scanner.provider_client import request_benchmark_bars, request_market_data
from agents.scanner.settings import ScannerSettings
from agents.scanner.store import write_scan
from agents.scanner.universe import StaticUniverse
from contracts.common import Explanation, ScanRequest, Window
from contracts.scanner import CONTRACT, Candidate, CandidateSet, FilterTrace
from kernel import (
    AgentBase,
    CollectingFaultSink,
    FaultSink,
    GraphStore,
    claim_check_write,
)
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from pydantic import BaseModel

    from agents.scanner.universe import UniverseSource
    from contracts.provider import MarketData
    from kernel import MessageBus


class ScannerAgent(AgentBase):
    """Universe-reduction scanner agent."""

    def __init__(
        self,
        bus: MessageBus,
        *,
        graph: GraphStore,
        universe: UniverseSource | None = None,
        settings: ScannerSettings | None = None,
        sink: FaultSink | None = None,
    ) -> None:
        """Create a scanner with injected bus, graph, universe, settings, and sink."""
        super().__init__(CONTRACT, bus)
        self._graph = graph
        self._universe = universe if universe is not None else StaticUniverse()
        self._settings = settings or ScannerSettings()
        self.sink = sink if sink is not None else CollectingFaultSink()
        self.handlers = {
            "run_scan": self._run_scan,
            "explain_filter": self._explain_filter,
        }

    def bind(self) -> None:
        """Register RPC handlers and subscribe to run.trigger for pub/sub mode."""
        super().bind()
        self.bus.subscribe("run.trigger", self._on_run_trigger)

    def _on_run_trigger(self, event: dict[str, Any]) -> None:
        run_id: str | None = event.get("run_id")
        req = ScanRequest(
            run_id=str(run_id) if run_id else uuid.uuid4().hex,
            universe=str(event.get("universe", "sp500")),
        )
        candidates = self._run_scan(req)
        claim_check_write(
            self.bus,
            self._graph,
            topic="scan.candidates.ready",
            label="ScanResult",
            ref=f"scan:{req.run_id}",
            props={"candidates": candidates.model_dump(mode="json")},
            run_id=run_id,
        )

    def _run_scan(self, request: BaseModel) -> CandidateSet:
        scan_request = ScanRequest.model_validate(request)
        tickers = self._universe.members(scan_request.universe)
        window = self._window()
        market = request_market_data(self.bus, self.sink, tickers, window)
        if market is None or market.quality.used_fallback:
            if market is not None:
                self._record_provider_degraded()
            return self._empty_result(scan_request, tickers, market)
        benchmark_bars = request_benchmark_bars(
            self.bus, self.sink, self._settings.benchmark_ticker, window
        )
        survivors, trace = apply_filters(
            tickers,
            market.bars,
            benchmark_bars,
            market.earnings,
            window.end,
            self._settings,
        )
        candidates = rank_survivors(survivors, cap=self._settings.candidate_cap)
        provenance = write_scan(
            self._graph,
            universe=scan_request.universe,
            candidates=candidates,
            trace=trace,
            provider_graph_node_id=market.provenance.graph_node_id,
        )
        return CandidateSet(
            run_id=provenance.run_id,
            candidates=candidates,
            filter_trace=trace,
            explanation=_scan_explanation(candidates, trace),
            provenance=provenance,
        )

    def _explain_filter(self, request: BaseModel) -> Explanation:
        scan_request = ScanRequest.model_validate(request)
        tickers = self._universe.members(scan_request.universe)
        return Explanation(
            summary=(
                f"Scanner applies price >= {self._settings.min_price}, average "
                f"volume >= {self._settings.min_average_volume:.0f}, relative "
                f"strength >= {self._settings.min_relative_strength:.3f}, "
                f"beta <= {self._settings.max_beta:.2f}, and excludes names with "
                f"earnings within {self._settings.earnings_exclusion_days} days, to "
                f"{len(tickers)} configured {scan_request.universe} members."
            ),
            evidence_refs=("scanner.filters.core",),
        )

    def _record_provider_degraded(self) -> None:
        with fault_boundary(
            self.sink,
            agent="scanner",
            module="agents.scanner.agent",
            capability="run_scan",
            reraise=False,
        ):
            raise RuntimeError("provider returned degraded market data")

    def _empty_result(
        self,
        request: ScanRequest,
        tickers: tuple[str, ...],
        market: MarketData | None,
    ) -> CandidateSet:
        trace = FilterTrace(
            universe_size=len(tickers),
            evaluated=0,
            dropped_by_filter={"provider_degraded": len(tickers)} if tickers else {},
        )
        provenance = write_scan(
            self._graph,
            universe=request.universe,
            candidates=(),
            trace=trace,
            provider_graph_node_id=(
                None if market is None else market.provenance.graph_node_id
            ),
        )
        return CandidateSet(
            run_id=provenance.run_id,
            candidates=(),
            filter_trace=trace,
            explanation=Explanation(
                summary=(
                    "No candidates: provider market data was unavailable or degraded."
                ),
                evidence_refs=("provider.get_market_data",),
            ),
            provenance=provenance,
        )

    def _window(self) -> Window:
        end = datetime.now(tz=UTC).date()
        start = end - timedelta(days=self._settings.lookback_days)
        return Window(start=start, end=end)


def _scan_explanation(
    candidates: tuple[Candidate, ...], trace: FilterTrace
) -> Explanation:
    if not candidates:
        return Explanation(
            summary="No candidates survived the scanner filters.",
            evidence_refs=("scanner.filters.core",),
        )
    return Explanation(
        summary=(
            f"{len(candidates)} candidates survived from {trace.evaluated} evaluated "
            "tickers using price, liquidity, relative-strength, beta, and "
            "earnings-window filters."
        ),
        evidence_refs=("scanner.filters.core",),
    )
