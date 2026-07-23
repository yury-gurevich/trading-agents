"""Portfolio Manager test helpers.

Agent: portfolio_manager
Role: provide deterministic PM fixtures and in-process wiring.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from agents.portfolio_manager import PortfolioManagerAgent
from agents.portfolio_manager.portfolio import PortfolioState
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from contracts.analyst import Recommendation, RecommendationSet
from contracts.common import Explanation, Money, Provenance
from contracts.provider import OHLCVBar
from kernel import AgentMessage, CollectingFaultSink, InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from agents.portfolio_manager.settings import PortfolioManagerSettings


def bar(ticker: str, days_ago: int, close: float) -> OHLCVBar:
    day = datetime.now(tz=UTC).date() - timedelta(days=days_ago)
    open_ = close * 0.95
    return OHLCVBar(
        ticker=ticker,
        bar_date=day,
        open=open_,
        high=max(open_, close) + 1.0,
        low=min(open_, close) - 1.0,
        close=close,
        volume=1_000_000,
    )


def recommendation(ticker: str = "AAPL", confidence: float = 0.80) -> Recommendation:
    return Recommendation(
        ticker=ticker,
        action="buy",
        confidence=confidence,
        technical_score=0.75,
        rationale=Explanation(summary="fixture recommendation"),
    )


def recommendation_set(*recommendations: Recommendation) -> RecommendationSet:
    return RecommendationSet(
        run_id="analyst-run-fixture",
        recommendations=recommendations,
        rejections=(),
        explanation=Explanation(summary="fixture analysis"),
        provenance=Provenance(
            run_id="analyst-run-fixture",
            source_agent="analyst",
            graph_node_id="AnalystRun:analyst-run-fixture",
        ),
    )


def seed_recommendation_nodes(
    graph: InMemoryGraphStore, payload: RecommendationSet
) -> None:
    graph.merge_node("AnalystRun", payload.run_id, {"recommendation_count": 1})
    for item in payload.recommendations:
        graph.merge_node(
            "Recommendation",
            f"{payload.run_id}:{item.ticker}",
            {"ticker": item.ticker, "confidence": item.confidence},
        )


def evaluate_message(payload: RecommendationSet) -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="portfolio_manager",
        message_type="request",
        capability="evaluate_orders",
        payload=payload.model_dump(mode="json"),
    )


def explain_message(payload: RecommendationSet) -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="portfolio_manager",
        message_type="request",
        capability="explain_decision",
        payload=payload.model_dump(mode="json"),
    )


def wire_pm(
    *,
    source_bars: tuple[OHLCVBar, ...] = (),
    sectors: dict[str, str] | None = None,
    settings: PortfolioManagerSettings | None = None,
    portfolio: PortfolioState | None = None,
    fail_ohlcv: bool = False,
    fail_regime: bool = False,
) -> tuple[InProcessBus, InMemoryGraphStore, CollectingFaultSink]:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    ProviderAgent(
        bus,
        graph=graph,
        source=FakeDataSource(
            bars=source_bars,
            vix=12.0,
            sectors=sectors,
            fail_ohlcv=fail_ohlcv,
            fail_regime=fail_regime,
        ),
        settings=ProviderSettings(max_staleness_days=7),
    ).bind()
    PortfolioManagerAgent(
        bus,
        graph=graph,
        settings=settings,
        portfolio=portfolio,
        sink=sink,
    ).bind()
    return bus, graph, sink


def cash_portfolio(
    amount: str,
    positions: dict[str, int] | None = None,
    position_refs: dict[str, str] | None = None,
) -> PortfolioState:
    return PortfolioState(
        cash=Money(amount=Decimal(amount)),
        positions=positions or {},
        position_refs=position_refs or {},
    )
