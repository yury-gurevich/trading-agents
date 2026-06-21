"""Portfolio Manager sizing+risk core shared by the bus and graph-pull paths.

Agent: portfolio_manager
Role: given a recommendation set plus already-acquired market+regime, size, risk-check,
      and persist the PM run. Called by the bus handler (`_evaluate_orders`) and the
      graph-pull poll path (`evaluate_analyst_node`) so both stay consistent (DL-08b).
External I/O: none (writes via the injected GraphStore).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.provider_client import latest_close_prices
from agents.portfolio_manager.result import build_order_set, incident_refs, reject_all
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from agents.portfolio_manager.portfolio import PortfolioState
    from agents.portfolio_manager.settings import PortfolioManagerSettings
    from contracts.analyst import RecommendationSet
    from contracts.portfolio_manager import OrderIntent, OrderIntentSet, RejectedOrder
    from contracts.provider import MarketData, RegimeContext
    from kernel import FaultSink, GraphStore


def run_evaluation(
    graph: GraphStore,
    *,
    recommendation_set: RecommendationSet,
    market: MarketData | None,
    regime: RegimeContext | None,
    settings: PortfolioManagerSettings,
    portfolio: PortfolioState,
    sink: FaultSink,
) -> OrderIntentSet:
    """Size+risk-check recommendations against acquired market+regime; persist."""
    if not recommendation_set.recommendations:
        return reject_all(
            graph, recommendation_set=recommendation_set, reason="no_recommendations"
        )
    refs = incident_refs(market, regime)
    rejection = _provider_rejection(sink, market, regime)
    if rejection is not None:
        return reject_all(
            graph,
            recommendation_set=recommendation_set,
            reason=rejection,
            incident_refs=refs,
        )
    assert market is not None
    assert regime is not None
    approved: tuple[OrderIntent, ...] = ()
    rejected: tuple[RejectedOrder, ...] = ()
    with fault_boundary(
        sink,
        agent="portfolio_manager",
        module="agents.portfolio_manager.run",
        capability="evaluate_orders",
        reraise=False,
    ) as capture:
        approved, rejected = evaluate_recommendations(
            recommendation_set.recommendations,
            latest_close_prices(market),
            portfolio,
            max_position_pct=settings.max_position_pct,
            max_positions=settings.max_positions,
            cash_buffer_pct=settings.cash_buffer_pct,
            min_order_quantity=settings.min_order_quantity,
            default_stop_pct=regime.base_stop_loss_pct,
            default_target_pct=regime.base_take_profit_pct,
            min_reward_risk_ratio=settings.min_reward_risk_ratio,
            sectors=market.sectors,
            max_sector_pct=settings.max_sector_pct,
        )
    if capture.fault is not None:
        return reject_all(
            graph,
            recommendation_set=recommendation_set,
            reason="portfolio_evaluation_failed",
            incident_refs=refs,
        )
    return build_order_set(
        graph,
        recommendation_set=recommendation_set,
        approved=approved,
        rejected=rejected,
        incident_refs=refs,
    )


def _provider_rejection(
    sink: FaultSink, market: MarketData | None, regime: RegimeContext | None
) -> str | None:
    """Return a portfolio-level rejection reason when provider data is unusable."""
    if market is None or regime is None:
        return "provider_unavailable"
    if market.quality.used_fallback:
        _record_fault(sink, "provider returned degraded market data")
        return "provider_degraded"
    if regime.provenance.incident_refs:
        _record_fault(sink, "provider returned degraded regime data")
        return "provider_degraded"
    return None


def _record_fault(sink: FaultSink, message: str) -> None:
    """Record a degraded-provider fault without interrupting evaluation."""
    with fault_boundary(
        sink,
        agent="portfolio_manager",
        module="agents.portfolio_manager.run",
        capability="evaluate_orders",
        reraise=False,
    ):
        raise RuntimeError(message)
