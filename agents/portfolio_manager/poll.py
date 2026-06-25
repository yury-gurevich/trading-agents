"""Portfolio Manager graph-poll work source (DL-08 / DL-08b).

Agent: portfolio_manager
Role: find AnalystRun nodes the PM has not evaluated yet and size+risk-check them
      straight from the graph — reading the analyst's RecommendationSet, the
      provider's MarketData (via the AnalystRun's ScanRun lineage) and same-day
      RegimeContext — with no live bus RPC, so neither the analyst nor the provider
      need be alive.
External I/O: none (reads/writes the injected GraphStore).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.portfolio_manager.portfolio import default_portfolio
from agents.portfolio_manager.run import run_evaluation
from agents.portfolio_manager.settings import PortfolioManagerSettings
from contracts.analyst import RecommendationSet
from contracts.provider import REGIME_CONTEXT_LABEL, MarketData, RegimeContext
from kernel import CollectingFaultSink

if TYPE_CHECKING:
    from agents.portfolio_manager.portfolio import PortfolioState
    from kernel import FaultSink, GraphStore, Node

ANALYST_RUN_LABEL = "AnalystRun"
EVALUATED_EDGE = "EVALUATED_BY"
_ANALYZED_EDGE = "ANALYZED_BY"
_DERIVED_FROM = "DERIVED_FROM"


def find_pending(graph: GraphStore) -> list[Node]:
    """Return AnalystRun nodes with no downstream PMRun (unprocessed work)."""
    pending: list[Node] = []
    for node in graph.list_nodes(ANALYST_RUN_LABEL):
        evaluated = list(
            graph.descendants(node, max_depth=1, edge_types={EVALUATED_EDGE})
        )
        if not evaluated:
            pending.append(node)
    return pending


def evaluate_analyst_node(
    node: Node,
    *,
    graph: GraphStore,
    settings: PortfolioManagerSettings | None = None,
    portfolio: PortfolioState | None = None,
    sink: FaultSink | None = None,
) -> None:
    """Evaluate one AnalystRun node from the graph and link the PMRun back to it."""
    settings = settings or PortfolioManagerSettings()
    sink = sink if sink is not None else CollectingFaultSink()
    portfolio = portfolio or default_portfolio(settings.starting_cash)
    recommendation_set = RecommendationSet.model_validate(
        node.props["recommendation_set"]
    )
    market, regime = _market_and_regime(graph, node)
    result = run_evaluation(
        graph,
        recommendation_set=recommendation_set,
        market=market,
        regime=regime,
        settings=settings,
        portfolio=portfolio,
        sink=sink,
    )
    # Persist the full OrderIntentSet on the PMRun so execution can pull it from the
    # graph (DL-08b) instead of receiving it as a bus payload.
    pm_run = graph.merge_node(
        "PMRun", result.run_id, {"order_intent_set": result.model_dump(mode="json")}
    )
    graph.add_edge(node, pm_run, EVALUATED_EDGE)


def _market_and_regime(
    graph: GraphStore, analyst_run: Node
) -> tuple[MarketData | None, RegimeContext | None]:
    # write_analysis links (scan)-[:ANALYZED_BY]->(analyst), and write_scan links
    # (scan)-[:DERIVED_FROM]->(market), so the MarketData the analyst consumed is the
    # ANALYZED_BY ancestor's DERIVED_FROM descendant. Regime is keyed by window_end.
    scan_run = next(
        iter(graph.ancestors(analyst_run, max_depth=1, edge_types={_ANALYZED_EDGE})),
        None,
    )
    if scan_run is None:
        return None, None
    market_node = next(
        iter(graph.descendants(scan_run, max_depth=1, edge_types={_DERIVED_FROM})),
        None,
    )
    if market_node is None:
        return None, None
    market = MarketData.model_validate(market_node.props["snapshot"])
    regime_node = graph.get_node(
        REGIME_CONTEXT_LABEL, f"regime-context:{market_node.props['run_id']}"
    )
    regime = (
        RegimeContext.model_validate(regime_node.props["snapshot"])
        if regime_node
        else None
    )
    return market, regime
