"""Portfolio Manager response assembly helpers.

Agent: portfolio_manager
Role: build OrderIntentSet payloads and run-level explanations.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.portfolio_manager.store import write_order_decision
from contracts.common import Explanation
from contracts.portfolio_manager import OrderIntentSet, RejectedOrder

if TYPE_CHECKING:
    from contracts.analyst import RecommendationSet
    from contracts.portfolio_manager import OrderIntent
    from contracts.provider import MarketData, RegimeContext
    from kernel import GraphStore


def build_order_set(
    graph: GraphStore,
    *,
    recommendation_set: RecommendationSet,
    approved: tuple[OrderIntent, ...],
    rejected: tuple[RejectedOrder, ...],
    incident_refs: tuple[str, ...] = (),
) -> OrderIntentSet:
    """Persist a PM decision and build its response payload."""
    provenance = write_order_decision(
        graph,
        recommendation_set=recommendation_set,
        approved=approved,
        rejected=rejected,
        incident_refs=incident_refs,
    )
    return OrderIntentSet(
        run_id=provenance.run_id,
        approved=approved,
        rejected=rejected,
        explanation=run_explanation(approved, rejected),
        provenance=provenance,
    )


def reject_all(
    graph: GraphStore,
    *,
    recommendation_set: RecommendationSet,
    reason: str,
    incident_refs: tuple[str, ...] = (),
) -> OrderIntentSet:
    """Reject every recommendation with one portfolio-level reason."""
    rejected = tuple(
        RejectedOrder(ticker=item.ticker, reason=reason)
        for item in recommendation_set.recommendations
    )
    return build_order_set(
        graph,
        recommendation_set=recommendation_set,
        approved=(),
        rejected=rejected,
        incident_refs=incident_refs,
    )


def run_explanation(
    approved: tuple[OrderIntent, ...], rejected: tuple[RejectedOrder, ...]
) -> Explanation:
    """Build the run-level PM explanation."""
    if not approved:
        return Explanation(
            summary=f"No orders approved; {len(rejected)} recommendations rejected.",
            evidence_refs=("portfolio_manager.risk",),
        )
    return Explanation(
        summary=(
            f"{len(approved)} orders approved; {len(rejected)} rejected by PM risk."
        ),
        evidence_refs=("portfolio_manager.sizing", "portfolio_manager.risk"),
    )


def incident_refs(
    market: MarketData | None, regime: RegimeContext | None
) -> tuple[str, ...]:
    """Combine provider incident refs without duplicates."""
    refs: list[str] = []
    if market is not None:
        refs.extend(market.provenance.incident_refs)
    if regime is not None:
        refs.extend(regime.provenance.incident_refs)
    return tuple(dict.fromkeys(refs))
