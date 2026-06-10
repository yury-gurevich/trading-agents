"""Portfolio Manager graph write path.

Agent: portfolio_manager
Role: write PM runs, order intents, rejection evidence, and recommendation lineage.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

from contracts.common import Money, Provenance

if TYPE_CHECKING:
    from contracts.analyst import RecommendationSet
    from contracts.portfolio_manager import OrderIntent, RejectedOrder
    from kernel import GraphStore, Node

CENTS_PER_DOLLAR = Decimal("100")


def write_order_decision(
    graph: GraphStore,
    *,
    recommendation_set: RecommendationSet,
    approved: tuple[OrderIntent, ...],
    rejected: tuple[RejectedOrder, ...],
    incident_refs: tuple[str, ...] = (),
) -> Provenance:
    """Write one PM run and approved order intents into the graph."""
    run_id = f"pm-run-{uuid.uuid4().hex}"
    run = graph.merge_node(
        "PMRun",
        run_id,
        {
            "approved_count": len(approved),
            "rejected_count": len(rejected),
            "source_analyst_run_id": recommendation_set.run_id,
            "created_at": datetime.now(tz=UTC).isoformat(),
        },
    )
    analyst_key = _analyst_key(recommendation_set)
    for order in approved:
        node = graph.merge_node(
            "OrderIntent",
            f"{run_id}:{order.ticker}",
            {
                "ticker": order.ticker,
                "action": order.action,
                "quantity": order.quantity,
                "est_price_cents": _money_to_cents(order.est_price),
                "est_price_currency": order.est_price.currency,
                "stop_pct": order.stop_pct,
                "target_pct": order.target_pct,
            },
        )
        graph.add_edge(node, run, "EMITTED_BY")
        _link_recommendation(graph, node, analyst_key, order.ticker, "APPROVES")
    for rejection in rejected:
        node = graph.merge_node(
            "Rejection",
            f"{run_id}:{rejection.ticker}",
            {"ticker": rejection.ticker, "reason": rejection.reason},
        )
        graph.add_edge(node, run, "REJECTED_IN")
        _link_recommendation(graph, node, analyst_key, rejection.ticker, "REJECTS")
    return Provenance(
        run_id=run_id,
        source_agent="portfolio_manager",
        graph_node_id=f"{run.label}:{run.key}",
        incident_refs=incident_refs,
    )


def _money_to_cents(money: Money) -> int:
    cents = (money.amount * CENTS_PER_DOLLAR).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )
    return int(cents)


def _analyst_key(recommendation_set: RecommendationSet) -> str | None:
    graph_id = recommendation_set.provenance.graph_node_id
    if graph_id is None or not graph_id.startswith("AnalystRun:"):
        return None
    return graph_id.split(":", 1)[1]


def _link_recommendation(
    graph: GraphStore,
    node: Node,
    analyst_key: str | None,
    ticker: str,
    edge_type: str,
) -> None:
    if analyst_key is None:
        return
    recommendation = graph.get_node("Recommendation", f"{analyst_key}:{ticker}")
    if recommendation is not None:
        graph.add_edge(node, recommendation, edge_type)
