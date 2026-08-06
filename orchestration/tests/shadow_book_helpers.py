"""Deterministic graph fixtures for shadow-book tests.

Agent: orchestration
Role: seed analyst, PM, and market facts without invoking trading behavior.
External I/O: none.
"""

from __future__ import annotations

from collections import Counter
from decimal import Decimal
from typing import TYPE_CHECKING

from contracts.analyst import Recommendation, RecommendationSet
from contracts.common import Explanation, Money, Provenance
from contracts.portfolio_manager import OrderIntent, OrderIntentSet, RejectedOrder
from contracts.provider import DataQualityTrace, MarketData, OHLCVBar

if TYPE_CHECKING:
    from datetime import date

    from contracts.common import Action
    from kernel import InMemoryGraphStore, Node


def recommendation(
    ticker: str, *, action: Action = "buy", confidence: float = 0.62
) -> Recommendation:
    """Build one recommendation with the contract's required evidence."""
    return Recommendation(
        ticker=ticker,
        action=action,
        confidence=confidence,
        technical_score=0.75,
        rationale=Explanation(summary=f"fixture {ticker}"),
    )


def bar(ticker: str, bar_date: date, close: float) -> OHLCVBar:
    """Build one valid daily close."""
    return OHLCVBar(
        ticker=ticker,
        bar_date=bar_date,
        open=close,
        high=close,
        low=close,
        close=close,
        volume=1_000,
    )


def add_market(
    graph: InMemoryGraphStore,
    key: str,
    window_end: date,
    bars: tuple[OHLCVBar, ...],
) -> Node:
    """Persist one immutable MarketData fixture node."""
    market = MarketData(
        bars=bars,
        quality=DataQualityTrace(requested=len(bars), returned=len(bars)),
        provenance=Provenance(run_id=key, source_agent="provider"),
    )
    return graph.merge_node(
        "MarketData",
        key,
        {
            "snapshot": market.model_dump(mode="json"),
            "tickers": sorted({item.ticker for item in bars}),
            "window_end": window_end.isoformat(),
            "run_id": key,
        },
    )


def seed_run(
    graph: InMemoryGraphStore,
    run_id: str,
    as_of: date,
    recommendations: tuple[Recommendation, ...],
    own_bars: tuple[OHLCVBar, ...],
    *,
    approved: tuple[str, ...] = (),
    rejected: tuple[tuple[str, str], ...] = (),
    include_pm: bool = True,
    create_scan: bool = True,
    link_market: bool = True,
) -> Node:
    """Seed one joined analyst run and its recorded PM disposition."""
    scan_id = f"scan-{run_id}"
    market = add_market(graph, f"market-{run_id}", as_of, own_bars)
    rec_set = RecommendationSet(
        run_id=run_id,
        recommendations=recommendations,
        rejections=(),
        explanation=Explanation(summary="fixture recommendations"),
        provenance=Provenance(
            run_id=run_id,
            source_agent="analyst",
            graph_node_id=f"AnalystRun:{run_id}",
        ),
    )
    analyst = graph.merge_node(
        "AnalystRun",
        run_id,
        {
            "created_at": f"{as_of.isoformat()}T20:00:00+00:00",
            "source_scan_run_id": scan_id,
            "recommendation_set": rec_set.model_dump(mode="json"),
        },
    )
    for item in recommendations:
        graph.merge_node(
            "Recommendation",
            f"{run_id}:{item.ticker}",
            {
                "ticker": item.ticker,
                "action": item.action,
                "confidence": item.confidence,
                "technical_score": item.technical_score,
                "exit_trigger": item.exit_trigger,
                "quant_metrics": [],
            },
        )
    if create_scan:
        scan = graph.merge_node("ScanRun", scan_id, {})
        graph.add_edge(scan, analyst, "ANALYZED_BY")
        if link_market:
            graph.add_edge(scan, market, "DERIVED_FROM")
    if include_pm:
        _seed_pm(graph, analyst, rec_set, approved, rejected)
    return analyst


def _seed_pm(
    graph: InMemoryGraphStore,
    analyst: Node,
    rec_set: RecommendationSet,
    approved: tuple[str, ...],
    rejected: tuple[tuple[str, str], ...],
) -> None:
    orders = OrderIntentSet(
        run_id=f"pm-{analyst.key}",
        approved=tuple(_order(ticker) for ticker in approved),
        rejected=tuple(
            RejectedOrder(ticker=ticker, reason=reason) for ticker, reason in rejected
        ),
        explanation=Explanation(summary="recorded PM decision"),
        provenance=Provenance(
            run_id=f"pm-{analyst.key}", source_agent="portfolio_manager"
        ),
    )
    pm = graph.merge_node(
        "PMRun",
        orders.run_id,
        {
            "source_analyst_run_id": rec_set.run_id,
            "order_intent_set": orders.model_dump(mode="json"),
        },
    )
    graph.add_edge(analyst, pm, "EVALUATED_BY")


def _order(ticker: str) -> OrderIntent:
    return OrderIntent(
        ticker=ticker,
        action="buy",
        quantity=1,
        est_price=Money(amount=Decimal("100.00")),
        rationale=Explanation(summary="fixture approval"),
    )


def graph_census(
    graph: InMemoryGraphStore,
) -> tuple[Counter[str], Counter[tuple[str, str, str]]]:
    """Count nodes per label and edges per label signature."""
    nodes = Counter(node.label for node in graph._nodes.values())
    edges = Counter(
        (edge.parent[0], edge.edge_type, edge.child[0]) for edge in graph._edges
    )
    return nodes, edges
