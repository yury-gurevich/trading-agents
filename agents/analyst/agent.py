"""Analyst agent implementation.

Agent: analyst
Role: request provider facts over the bus and score scanner candidates.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from agents.analyst.domain.recommend import AnalysisDecision, decide
from agents.analyst.domain.scoring import score_candidate
from agents.analyst.provider_client import request_market_data, request_regime
from agents.analyst.result import (
    build_empty_result,
    incident_refs,
    run_explanation,
    split_decisions,
)
from agents.analyst.settings import AnalystSettings
from agents.analyst.store import write_analysis
from contracts.analyst import CONTRACT, RecommendationSet
from contracts.common import Explanation, Window
from contracts.scanner import CandidateSet
from kernel import AgentBase, CollectingFaultSink, FaultSink, GraphStore
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from pydantic import BaseModel

    from contracts.provider import MarketData, OHLCVBar, RegimeContext
    from kernel import MessageBus


class AnalystAgent(AgentBase):
    """Technical analyst boundary agent."""

    def __init__(
        self,
        bus: MessageBus,
        *,
        graph: GraphStore,
        settings: AnalystSettings | None = None,
        sink: FaultSink | None = None,
    ) -> None:
        """Create an analyst with injected bus, graph, settings, and sink."""
        super().__init__(CONTRACT, bus)
        self._graph = graph
        self._settings = settings or AnalystSettings()
        self.sink = sink if sink is not None else CollectingFaultSink()
        self.handlers = {
            "analyze": self._analyze,
            "explain_recommendation": self._explain_recommendation,
        }

    def _analyze(self, request: BaseModel) -> RecommendationSet:
        candidate_set = CandidateSet.model_validate(request)
        if not candidate_set.candidates:
            return build_empty_result(
                self._graph, candidate_set, "scanner produced no candidates"
            )

        market = request_market_data(self.bus, self.sink, candidate_set, self._window())
        regime = request_regime(self.bus, self.sink, self._window().end)
        refs = incident_refs(market, regime)
        if market is None or regime is None:
            return build_empty_result(
                self._graph, candidate_set, "provider data unavailable", refs
            )
        if market.quality.used_fallback:
            self._record_fault("provider returned degraded market data")
            return build_empty_result(
                self._graph,
                candidate_set,
                "provider market data degraded",
                refs or ("market_data_degraded",),
            )
        if regime.provenance.incident_refs:
            self._record_fault("provider regime data degraded")
            return build_empty_result(
                self._graph, candidate_set, "provider regime data degraded", refs
            )

        decisions = self._score(candidate_set, market, regime)
        if decisions is None:
            return build_empty_result(
                self._graph, candidate_set, "analyst scoring failed"
            )
        recommendations, rejections = split_decisions(decisions)
        provenance = write_analysis(
            self._graph,
            candidate_set=candidate_set,
            recommendations=recommendations,
            rejections=rejections,
            incident_refs=refs,
        )
        return RecommendationSet(
            run_id=provenance.run_id,
            recommendations=recommendations,
            rejections=rejections,
            explanation=run_explanation(recommendations, rejections, regime),
            provenance=provenance,
        )

    def _explain_recommendation(self, request: BaseModel) -> Explanation:
        candidate_set = CandidateSet.model_validate(request)
        return Explanation(
            summary=(
                "Analyst confidence blends a composite of RSI, MACD, Bollinger "
                "position, SMA-200 distance, and EMA crossover for "
                f"{len(candidate_set.candidates)} candidates, then gates each "
                "result against provider regime confidence."
            ),
            evidence_refs=("analyst.technical_score", "provider.regime"),
        )

    def _score(
        self,
        candidate_set: CandidateSet,
        market: MarketData,
        regime: RegimeContext,
    ) -> tuple[AnalysisDecision, ...] | None:
        decisions: tuple[AnalysisDecision, ...] = ()
        with fault_boundary(
            self.sink,
            agent="analyst",
            module="agents.analyst.agent",
            capability="analyze",
            reraise=False,
        ) as capture:
            bars = _bars_by_ticker(market.bars)
            decisions = tuple(
                decide(
                    candidate,
                    score_candidate(
                        candidate, bars.get(candidate.ticker, ()), self._settings
                    ),
                    regime,
                )
                for candidate in candidate_set.candidates
            )
        return None if capture.fault is not None else decisions

    def _record_fault(self, message: str) -> None:
        with fault_boundary(
            self.sink,
            agent="analyst",
            module="agents.analyst.agent",
            capability="analyze",
            reraise=False,
        ):
            raise RuntimeError(message)

    def _window(self) -> Window:
        end = datetime.now(tz=UTC).date()
        return Window(start=end - timedelta(days=self._settings.lookback_days), end=end)


def _bars_by_ticker(bars: tuple[OHLCVBar, ...]) -> dict[str, tuple[OHLCVBar, ...]]:
    grouped: dict[str, list[OHLCVBar]] = {}
    for bar in bars:
        grouped.setdefault(bar.ticker, []).append(bar)
    return {ticker: tuple(rows) for ticker, rows in grouped.items()}
