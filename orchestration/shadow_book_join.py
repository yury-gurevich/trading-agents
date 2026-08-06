"""Read-only graph joins for recommendation and PM facts.

Agent: orchestration
Role: align Recommendation nodes with AnalystRun and recorded OrderIntentSet facts.
External I/O: GraphStore reads via the injected backend; never writes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.portfolio_manager import OrderIntentSet

if TYPE_CHECKING:
    from kernel import GraphStore, Node

_RECOMMENDATION_LABEL = "Recommendation"
_PM_RUN_LABEL = "PMRun"


def recommendations_by_analyst(
    graph: GraphStore, analyst_runs: tuple[Node, ...]
) -> dict[str, tuple[Node, ...]]:
    """Join every Recommendation node to exactly one AnalystRun by its stable key."""
    grouped: dict[str, list[Node]] = {node.key: [] for node in analyst_runs}
    for recommendation in graph.list_nodes(_RECOMMENDATION_LABEL):
        ticker = str(recommendation.props["ticker"])
        suffix = f":{ticker}"
        if not recommendation.key.endswith(suffix):
            raise ValueError(f"malformed Recommendation key: {recommendation.key}")
        analyst_run_id = recommendation.key[: -len(suffix)]
        if analyst_run_id not in grouped:
            raise ValueError(
                f"Recommendation {recommendation.key} has no matching AnalystRun"
            )
        grouped[analyst_run_id].append(recommendation)
    return {
        run_id: tuple(sorted(nodes, key=lambda node: node.key))
        for run_id, nodes in grouped.items()
    }


def pm_orders_by_analyst(graph: GraphStore) -> dict[str, OrderIntentSet]:
    """Join each PMRun payload to its recorded source AnalystRun."""
    return {
        str(node.props["source_analyst_run_id"]): OrderIntentSet.model_validate(
            node.props["order_intent_set"]
        )
        for node in sorted(graph.list_nodes(_PM_RUN_LABEL), key=lambda item: item.key)
        if "source_analyst_run_id" in node.props
    }
