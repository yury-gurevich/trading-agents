"""Contract payloads for the S234 daily-brief fixtures, one per pipeline stage.

Agent: orchestration
Role: build the stage props a scheduled run's chain carries, from real contract models.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.analyst import RecommendationSet
from contracts.common import Explanation, Provenance
from contracts.portfolio_manager import OrderIntentSet, RejectedOrder
from contracts.position_sync import POSITION_SYNC_PHASE
from contracts.provider import DataQualityTrace, MarketData
from contracts.scanner import Candidate, CandidateSet, FilterTrace
from orchestration.tests.shadow_book_helpers import bar, recommendation

if TYPE_CHECKING:
    from datetime import date

    from contracts.portfolio_manager import OrderIntent

TICKER = "AAPL"


def stage_payloads(
    run_id: str,
    pm: str,
    day: date,
    approved: tuple[OrderIntent, ...],
    pm_created: str,
) -> dict[str, dict[str, object]]:
    """Return every stage's props, each a real contract model's dump."""

    def provenance(agent: str) -> Provenance:
        return Provenance(run_id=run_id, source_agent=agent)

    explanation = Explanation(summary="fixture")
    market = MarketData(
        bars=(bar(TICKER, day, 100.0),),
        quality=DataQualityTrace(requested=1, returned=1),
        provenance=provenance("provider"),
    )
    candidates = CandidateSet(
        run_id=run_id,
        candidates=(Candidate(ticker=TICKER, rank=1, score=1.0, survived_filters=()),),
        filter_trace=FilterTrace(universe_size=1, evaluated=1),
        explanation=explanation,
        provenance=provenance("scanner"),
    )
    recommendations = RecommendationSet(
        run_id=run_id,
        recommendations=(recommendation(TICKER),),
        rejections=(),
        explanation=explanation,
        provenance=provenance("analyst"),
    )
    intents = OrderIntentSet(
        run_id=pm,
        approved=approved,
        rejected=() if approved else (RejectedOrder(ticker=TICKER, reason="full"),),
        explanation=explanation,
        provenance=provenance("portfolio_manager"),
    )
    return {
        "PositionSync": {"phase": POSITION_SYNC_PHASE, "position_book_status": "fresh"},
        "MarketData": {"snapshot": market.model_dump(mode="json"), "tickers": [TICKER]},
        "ScanRun": {"candidate_set": candidates.model_dump(mode="json")},
        "AnalystRun": {"recommendation_set": recommendations.model_dump(mode="json")},
        "PMRun": {
            "order_intent_set": intents.model_dump(mode="json"),
            "created_at": pm_created,
        },
        "ExecutionRun": {
            "submitted": len(approved),
            "rejected": 0,
            "deliberation_posture": "advisory",
            "deliberation_status": "applied" if approved else "not_required",
        },
        "MonitorRun": {"positions_checked": 10, "closes": 0, "holds": 10},
    }
