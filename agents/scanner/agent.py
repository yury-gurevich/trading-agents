"""Scanner agent implementation.

Agent: scanner
Role: request provider market data over the bus and return ranked candidates.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from agents.scanner.domain.filters import apply_filters
from agents.scanner.domain.ranking import rank_survivors
from agents.scanner.settings import ScannerSettings
from agents.scanner.store import write_scan
from agents.scanner.universe import StaticUniverse
from contracts.common import Explanation, ScanRequest, Window
from contracts.provider import DataRequest, MarketData
from contracts.scanner import CONTRACT, Candidate, CandidateSet, FilterTrace
from kernel import AgentBase, AgentMessage, CollectingFaultSink, FaultSink, GraphStore
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from pydantic import BaseModel

    from agents.scanner.universe import UniverseSource
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

    def _run_scan(self, request: BaseModel) -> CandidateSet:
        scan_request = ScanRequest.model_validate(request)
        tickers = self._universe.members(scan_request.universe)
        market = self._request_market_data(tickers)
        if market is None or market.quality.used_fallback:
            if market is not None:
                self._record_provider_degraded()
            return self._empty_result(scan_request, tickers, market)
        survivors, trace = apply_filters(tickers, market.bars, self._settings)
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
                f"volume >= {self._settings.min_average_volume:.0f}, and "
                f"relative strength >= {self._settings.min_relative_strength:.3f} "
                f"to {len(tickers)} configured {scan_request.universe} members."
            ),
            evidence_refs=("scanner.filters.core",),
        )

    def _request_market_data(self, tickers: tuple[str, ...]) -> MarketData | None:
        market: MarketData | None = None
        with fault_boundary(
            self.sink,
            agent="scanner",
            module="agents.scanner.agent",
            capability="run_scan",
            reraise=False,
        ) as capture:
            response = self.bus.request(
                AgentMessage(
                    sender="scanner",
                    recipient="provider",
                    message_type="request",
                    capability="get_market_data",
                    payload=DataRequest(
                        tickers=tickers,
                        window=self._window(),
                    ).model_dump(mode="json"),
                )
            )
            if response.message_type == "error":
                message = str(response.payload.get("message", "provider error"))
                raise RuntimeError(message)
            market = MarketData.model_validate(response.payload)
        if capture.fault is not None:
            return None
        return market

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
            "tickers using price, liquidity, and relative-strength filters."
        ),
        evidence_refs=("scanner.filters.core",),
    )
