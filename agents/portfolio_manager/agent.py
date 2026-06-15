"""Portfolio Manager agent implementation.

Agent: portfolio_manager
Role: size and risk-check analyst recommendations into order intents.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.portfolio import PortfolioState, default_portfolio
from agents.portfolio_manager.provider_client import (
    latest_close_prices,
    request_market_data,
    request_regime,
)
from agents.portfolio_manager.result import build_order_set, incident_refs, reject_all
from agents.portfolio_manager.settings import PortfolioManagerSettings
from contracts.analyst import RecommendationSet
from contracts.common import Explanation, Window
from contracts.portfolio_manager import (
    CONTRACT,
    OrderIntent,
    OrderIntentSet,
    RejectedOrder,
)
from kernel import AgentBase, CollectingFaultSink, FaultSink, GraphStore
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from pydantic import BaseModel

    from contracts.provider import MarketData, RegimeContext
    from kernel import MessageBus


class PortfolioManagerAgent(AgentBase):
    """Portfolio manager boundary agent."""

    def __init__(
        self,
        bus: MessageBus,
        *,
        graph: GraphStore,
        settings: PortfolioManagerSettings | None = None,
        portfolio: PortfolioState | None = None,
        sink: FaultSink | None = None,
    ) -> None:
        """Create a PM with injected bus, graph, settings, portfolio, and sink."""
        super().__init__(CONTRACT, bus)
        self._graph = graph
        self._settings = settings or PortfolioManagerSettings()
        self._portfolio = portfolio or default_portfolio(self._settings.starting_cash)
        self.sink = sink if sink is not None else CollectingFaultSink()
        self.handlers = {
            "evaluate_orders": self._evaluate_orders,
            "explain_decision": self._explain_decision,
        }

    def _evaluate_orders(self, request: BaseModel) -> OrderIntentSet:
        recommendation_set = RecommendationSet.model_validate(request)
        if not recommendation_set.recommendations:
            return self._empty_result(recommendation_set, "no_recommendations")

        market = request_market_data(
            self.bus, self.sink, recommendation_set, self._window()
        )
        regime = request_regime(self.bus, self.sink, self._window().end)
        refs = incident_refs(market, regime)
        provider_rejection = self._provider_rejection(market, regime)
        if provider_rejection is not None:
            return reject_all(
                self._graph,
                recommendation_set=recommendation_set,
                reason=provider_rejection,
                incident_refs=refs,
            )

        assert market is not None
        assert regime is not None
        approved: tuple[OrderIntent, ...] = ()
        rejected: tuple[RejectedOrder, ...] = ()
        with fault_boundary(
            self.sink,
            agent="portfolio_manager",
            module="agents.portfolio_manager.agent",
            capability="evaluate_orders",
            reraise=False,
        ) as capture:
            approved, rejected = evaluate_recommendations(
                recommendation_set.recommendations,
                latest_close_prices(market),
                self._portfolio,
                max_position_pct=self._settings.max_position_pct,
                max_positions=self._settings.max_positions,
                cash_buffer_pct=self._settings.cash_buffer_pct,
                min_order_quantity=self._settings.min_order_quantity,
                default_stop_pct=regime.base_stop_loss_pct,
                default_target_pct=regime.base_take_profit_pct,
                min_reward_risk_ratio=self._settings.min_reward_risk_ratio,
            )
        if capture.fault is not None:
            return reject_all(
                self._graph,
                recommendation_set=recommendation_set,
                reason="portfolio_evaluation_failed",
                incident_refs=refs,
            )
        return build_order_set(
            self._graph,
            recommendation_set=recommendation_set,
            approved=approved,
            rejected=rejected,
            incident_refs=refs,
        )

    def _explain_decision(self, request: BaseModel) -> Explanation:
        recommendation_set = RecommendationSet.model_validate(request)
        return Explanation(
            summary=(
                "Portfolio manager requests latest price and regime policy from "
                "provider, sizes buy recommendations from portfolio value, then "
                f"checks cash buffer, max positions, and minimum quantity for "
                f"{len(recommendation_set.recommendations)} recommendations."
            ),
            evidence_refs=("provider.get_market_data", "provider.get_regime"),
        )

    def _provider_rejection(
        self, market: MarketData | None, regime: RegimeContext | None
    ) -> str | None:
        if market is None or regime is None:
            return "provider_unavailable"
        if market.quality.used_fallback:
            self._record_fault("provider returned degraded market data")
            return "provider_degraded"
        if regime.provenance.incident_refs:
            self._record_fault("provider returned degraded regime data")
            return "provider_degraded"
        return None

    def _record_fault(self, message: str) -> None:
        with fault_boundary(
            self.sink,
            agent="portfolio_manager",
            module="agents.portfolio_manager.agent",
            capability="evaluate_orders",
            reraise=False,
        ):
            raise RuntimeError(message)

    def _empty_result(
        self, recommendation_set: RecommendationSet, reason: str
    ) -> OrderIntentSet:
        return reject_all(
            self._graph,
            recommendation_set=recommendation_set,
            reason=reason,
        )

    def _window(self) -> Window:
        end = datetime.now(tz=UTC).date()
        return Window(
            start=end - timedelta(days=self._settings.price_lookback_days),
            end=end,
        )
