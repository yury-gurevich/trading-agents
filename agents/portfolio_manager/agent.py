"""Portfolio Manager agent implementation.

Agent: portfolio_manager
Role: size and risk-check recommendations into order intents via RPC, and publish
      portfolio.orders.ready claim-check events on analysis.recommendations.ready.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from agents.portfolio_manager.graph_portfolio import portfolio_from_graph
from agents.portfolio_manager.portfolio import PortfolioState, default_portfolio
from agents.portfolio_manager.provider_client import (
    request_market_data,
    request_regime,
)
from agents.portfolio_manager.pubsub import on_recommendations_ready
from agents.portfolio_manager.run import run_evaluation
from agents.portfolio_manager.settings import PortfolioManagerSettings
from contracts.analyst import RecommendationSet
from contracts.common import Explanation, Window
from contracts.portfolio_manager import CONTRACT, OrderIntentSet
from kernel import (
    AgentBase,
    CollectingFaultSink,
    FaultSink,
    GraphStore,
)

if TYPE_CHECKING:
    from pydantic import BaseModel

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
        self._portfolio = portfolio
        self.sink = sink if sink is not None else CollectingFaultSink()
        self.handlers = {
            "evaluate_orders": self._evaluate_orders,
            "explain_decision": self._explain_decision,
        }

    def bind(self) -> None:
        """Register RPC handlers and subscribe to analysis.recommendations.ready."""
        super().bind()
        self.bus.subscribe(
            "analysis.recommendations.ready", self._on_recommendations_ready
        )

    def _on_recommendations_ready(self, event: dict[str, Any]) -> None:
        on_recommendations_ready(self.bus, self._graph, self._evaluate_orders, event)

    def _evaluate_orders(self, request: BaseModel) -> OrderIntentSet:
        recommendation_set = RecommendationSet.model_validate(request)
        market = regime = None
        if recommendation_set.recommendations:
            market = request_market_data(
                self.bus, self.sink, recommendation_set, self._window()
            )
            regime = request_regime(self.bus, self.sink, self._window().end)
        return run_evaluation(
            self._graph,
            recommendation_set=recommendation_set,
            market=market,
            regime=regime,
            settings=self._settings,
            portfolio=self._current_portfolio(),
            sink=self.sink,
        )

    def _explain_decision(self, request: BaseModel) -> Explanation:
        recommendation_set = RecommendationSet.model_validate(request)
        return Explanation(
            summary=(
                "Portfolio manager requests latest price and regime policy from "
                "provider, sizes buy recommendations from portfolio value, then "
                "checks cash buffer, max positions, minimum quantity, reward/risk, "
                "and sector concentration for "
                f"{len(recommendation_set.recommendations)} recommendations."
            ),
            evidence_refs=("provider.get_market_data", "provider.get_regime"),
        )

    def _window(self) -> Window:
        end = datetime.now(tz=UTC).date()
        return Window(
            start=end - timedelta(days=self._settings.price_lookback_days),
            end=end,
        )

    def _current_portfolio(self) -> PortfolioState:
        if self._portfolio is not None:
            return self._portfolio
        if self._graph.list_nodes("Position"):
            return portfolio_from_graph(self._graph, self._settings.starting_cash)
        return default_portfolio(self._settings.starting_cash)
