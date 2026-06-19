"""Portfolio Manager pub/sub handler.

Agent: portfolio_manager
Role: resolve analysis.recommendations.ready claim-check events, evaluate orders,
      and publish portfolio.orders.ready via claim-check.
External I/O: none.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from contracts.analyst import RecommendationSet
from kernel import GraphStore, claim_check_read, claim_check_write

if TYPE_CHECKING:
    from collections.abc import Callable

    from contracts.portfolio_manager import OrderIntentSet
    from kernel import MessageBus


def on_recommendations_ready(
    bus: MessageBus,
    graph: GraphStore,
    evaluate_orders: Callable[[RecommendationSet], OrderIntentSet],
    event: dict[str, Any],
) -> None:
    """Handle analysis.recommendations.ready: evaluate orders and publish."""
    run_id: str | None = event.get("run_id")
    node = claim_check_read(graph, event)
    recs = RecommendationSet.model_validate(node.props["recommendations"])
    orders = evaluate_orders(recs)
    claim_check_write(
        bus,
        graph,
        topic="portfolio.orders.ready",
        label="OrderIntentResult",
        ref=f"orders:{run_id or uuid.uuid4().hex}",
        props={"orders": orders.model_dump(mode="json")},
        run_id=run_id,
    )
