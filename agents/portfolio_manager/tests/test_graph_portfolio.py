"""Portfolio Manager graph-derived position awareness tests.

Agent: portfolio_manager
Role: verify PM risk gates seed PortfolioState from reconciled Position nodes.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from agents.portfolio_manager.graph_portfolio import portfolio_from_graph
from agents.portfolio_manager.poll import evaluate_analyst_node
from agents.portfolio_manager.settings import PortfolioManagerSettings
from agents.portfolio_manager.tests.helpers import (
    bar,
    recommendation,
    recommendation_set,
)
from contracts.common import Provenance
from contracts.provider import (
    MARKET_DATA_LABEL,
    REGIME_CONTEXT_LABEL,
    DataQualityTrace,
    MarketData,
    RegimeContext,
)
from kernel import InMemoryGraphStore, Node


def test_portfolio_from_graph_filters_to_active_positions() -> None:
    graph = InMemoryGraphStore()
    _position(graph, "active:AMD", "AMD", 19)
    _position(graph, "absent:HPE", "HPE", 229, broker_absent=True)
    _position(graph, "superseded:CSCO", "CSCO", 88, broker_superseded_by="broker")
    _position(graph, "status:MRVL", "MRVL", 44, status="closed")
    closed = _position(graph, "closed:INTC", "INTC", 10)
    close = graph.merge_node("CloseDecision", "close:INTC", {"decision": "close"})
    graph.add_edge(close, closed, "CLOSES")

    portfolio = portfolio_from_graph(graph, Decimal("10000.00"))

    assert portfolio.positions == {"AMD": 19}
    assert portfolio.cash.amount == Decimal("10000.00")


def test_evaluate_analyst_node_uses_graph_positions_for_max_positions_gate() -> None:
    graph = InMemoryGraphStore()
    _position(graph, "broker:AMD:19:15924", "AMD", 19)
    analyst = _seed_analyst_run(graph)
    settings = PortfolioManagerSettings(
        starting_cash=Decimal("10000.00"),
        max_position_pct=Decimal("0.10"),
        max_positions=1,
    )

    evaluate_analyst_node(analyst, graph=graph, settings=settings)

    assert graph.list_nodes("OrderIntent") == ()
    rejections = graph.list_nodes("Rejection")
    assert [node.props["reason"] for node in rejections] == ["max_positions"]


def _seed_analyst_run(graph: InMemoryGraphStore) -> Node:
    recommendations = recommendation_set(recommendation("MSFT"))
    analyst = graph.merge_node(
        "AnalystRun",
        recommendations.run_id,
        {"recommendation_set": recommendations.model_dump(mode="json")},
    )
    scan = graph.merge_node("ScanRun", "scan-1", {})
    graph.add_edge(scan, analyst, "ANALYZED_BY")
    market = MarketData(
        bars=(bar("MSFT", 0, 100.0),),
        quality=DataQualityTrace(requested=1, returned=1),
        provenance=Provenance(run_id="provider-md", source_agent="provider"),
    )
    market_node = graph.merge_node(
        MARKET_DATA_LABEL,
        "market-data:pm-graph",
        {
            "snapshot": market.model_dump(mode="json"),
            "window_end": "2026-07-08",
            "run_id": "pm-graph",
        },
    )
    graph.add_edge(scan, market_node, "DERIVED_FROM")
    regime = RegimeContext(
        label="neutral",
        as_of=datetime.now(tz=UTC),
        base_min_confidence=0.55,
        base_stop_loss_pct=0.05,
        base_take_profit_pct=0.10,
        base_max_holding_days=10,
        provenance=Provenance(run_id="provider-rg", source_agent="provider"),
    )
    graph.merge_node(
        REGIME_CONTEXT_LABEL,
        "regime-context:pm-graph",
        {"snapshot": regime.model_dump(mode="json"), "run_id": "pm-graph"},
    )
    return analyst


def _position(
    graph: InMemoryGraphStore,
    key: str,
    ticker: str,
    quantity: int,
    **extra: object,
) -> Node:
    return graph.merge_node(
        "Position",
        key,
        {
            "ticker": ticker,
            "quantity": quantity,
            "opened_price_cents": 10000,
            "status": "open",
            **extra,
        },
    )
