"""Portfolio Manager graph-poll find_pending + evaluate_analyst_node tests.

Agent: portfolio_manager
Role: verify the PM finds unevaluated AnalystRun nodes and sizes+risk-checks them
      from the graph (RecommendationSet + MarketData via the ScanRun lineage +
      same-day RegimeContext), marking each processed so it is not re-evaluated.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from agents.portfolio_manager.poll import evaluate_analyst_node, find_pending
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
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from contracts.analyst import RecommendationSet
    from kernel import GraphStore, Node

_WINDOW_END = "2026-06-22"


def _market_data() -> MarketData:
    return MarketData(
        bars=(bar("AAPL", 0, 100.0),),
        quality=DataQualityTrace(requested=1, returned=1),
        provenance=Provenance(run_id="provider-md", source_agent="provider"),
    )


def _regime() -> RegimeContext:
    return RegimeContext(
        label="neutral",
        as_of=datetime.now(tz=UTC),
        base_min_confidence=0.55,
        base_stop_loss_pct=0.05,
        base_take_profit_pct=0.10,
        base_max_holding_days=10,
        provenance=Provenance(run_id="provider-rg", source_agent="provider"),
    )


def _settings() -> PortfolioManagerSettings:
    return PortfolioManagerSettings(
        starting_cash=Decimal("10000.00"), max_position_pct=Decimal("0.10")
    )


def _seed_analyst_run(
    graph: GraphStore,
    *,
    payload: RecommendationSet | None = None,
    market: bool = True,
    regime: bool = True,
) -> Node:
    rset = payload or recommendation_set(recommendation("AAPL"))
    analyst_run = graph.merge_node(
        "AnalystRun",
        rset.run_id,
        {"recommendation_set": rset.model_dump(mode="json")},
    )
    scan_run = graph.merge_node("ScanRun", "scan-1", {})
    graph.add_edge(scan_run, analyst_run, "ANALYZED_BY")
    if market:
        market_node = graph.merge_node(
            MARKET_DATA_LABEL,
            f"market-data:{_WINDOW_END}",
            {
                "snapshot": _market_data().model_dump(mode="json"),
                "window_end": _WINDOW_END,
            },
        )
        graph.add_edge(scan_run, market_node, "DERIVED_FROM")
    if regime:
        graph.merge_node(
            REGIME_CONTEXT_LABEL,
            f"regime-context:{_WINDOW_END}",
            {"snapshot": _regime().model_dump(mode="json"), "window_end": _WINDOW_END},
        )
    return analyst_run


def test_find_pending_returns_unevaluated_analyst_run() -> None:
    graph = InMemoryGraphStore()
    _seed_analyst_run(graph)
    assert len(find_pending(graph)) == 1


def test_find_pending_empty_when_no_analyst_run() -> None:
    graph = InMemoryGraphStore()
    assert find_pending(graph) == []


def test_evaluate_analyst_node_sizes_orders_from_graph() -> None:
    graph = InMemoryGraphStore()
    node = _seed_analyst_run(graph)
    evaluate_analyst_node(node, graph=graph, settings=_settings())
    assert len(graph.list_nodes("PMRun")) == 1
    orders = graph.list_nodes("OrderIntent")
    assert [n.props["ticker"] for n in orders] == ["AAPL"]


def test_evaluate_analyst_node_marks_node_processed() -> None:
    graph = InMemoryGraphStore()
    node = _seed_analyst_run(graph)
    evaluate_analyst_node(node, graph=graph, settings=_settings())
    assert find_pending(graph) == []


def test_evaluate_analyst_node_empty_recommendations_still_writes_run() -> None:
    graph = InMemoryGraphStore()
    node = _seed_analyst_run(graph, payload=recommendation_set())
    evaluate_analyst_node(node, graph=graph, settings=_settings())
    assert len(graph.list_nodes("PMRun")) == 1
    assert find_pending(graph) == []


def test_evaluate_analyst_node_rejects_when_market_absent() -> None:
    graph = InMemoryGraphStore()
    node = _seed_analyst_run(graph, market=False)
    evaluate_analyst_node(node, graph=graph, settings=_settings())
    assert not graph.list_nodes("OrderIntent")
    rejections = graph.list_nodes("Rejection")
    assert [n.props["reason"] for n in rejections] == ["provider_unavailable"]


def test_evaluate_analyst_node_rejects_when_regime_absent() -> None:
    graph = InMemoryGraphStore()
    node = _seed_analyst_run(graph, regime=False)
    evaluate_analyst_node(node, graph=graph, settings=_settings())
    rejections = graph.list_nodes("Rejection")
    assert [n.props["reason"] for n in rejections] == ["provider_unavailable"]


def test_evaluate_analyst_node_rejects_when_scan_run_absent() -> None:
    graph = InMemoryGraphStore()
    rset = recommendation_set(recommendation("AAPL"))
    node = graph.merge_node(
        "AnalystRun",
        rset.run_id,
        {"recommendation_set": rset.model_dump(mode="json")},
    )
    evaluate_analyst_node(node, graph=graph, settings=_settings())
    rejections = graph.list_nodes("Rejection")
    assert [n.props["reason"] for n in rejections] == ["provider_unavailable"]
