"""Analyst agent implementation.

Agent: analyst
Role: request provider facts over the bus, score scanner candidates via RPC, and publish
      analysis.recommendations.ready claim-check events on scan.candidates.ready.
External I/O: none.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from agents.analyst.domain.analyze import score_candidates
from agents.analyst.domain.sentiment_reading import provider_reading
from agents.analyst.provider_client import (
    request_benchmark_bars,
    request_market_data,
    request_regime,
)
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
from kernel import (
    AgentBase,
    CollectingFaultSink,
    FaultSink,
    GraphStore,
    claim_check_read,
    claim_check_write,
)
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from pydantic import BaseModel

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

    def bind(self) -> None:
        """Register RPC handlers and subscribe to scan.candidates.ready."""
        super().bind()
        self.bus.subscribe("scan.candidates.ready", self._on_candidates_ready)

    def _on_candidates_ready(self, event: dict[str, Any]) -> None:
        run_id: str | None = event.get("run_id")
        node = claim_check_read(self._graph, event)
        candidates = CandidateSet.model_validate(node.props["candidates"])
        recs = self._analyze(candidates)
        claim_check_write(
            self.bus,
            self._graph,
            topic="analysis.recommendations.ready",
            label="RecommendationResult",
            ref=f"analysis:{run_id or uuid.uuid4().hex}",
            props={"recommendations": recs.model_dump(mode="json")},
            run_id=run_id,
        )

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

        benchmark_bars = request_benchmark_bars(
            self.bus, self.sink, self._settings.benchmark_ticker, self._window()
        )
        decisions = score_candidates(
            candidate_set, market, regime, benchmark_bars, self._settings, self.sink
        )
        if decisions is None:
            return build_empty_result(
                self._graph, candidate_set, "analyst scoring failed"
            )
        recommendations, rejections = split_decisions(decisions)
        lexicon_readings = tuple(
            decision.sentiment_reading
            for decision in decisions
            if decision.sentiment_reading is not None
        )
        provider_readings = tuple(
            provider_reading(candidate.ticker, market.sentiment[candidate.ticker])
            for candidate in candidate_set.candidates
            if candidate.ticker in market.sentiment
        )
        provenance = write_analysis(
            self._graph,
            candidate_set=candidate_set,
            recommendations=recommendations,
            rejections=rejections,
            sentiment_readings=lexicon_readings + provider_readings,
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
