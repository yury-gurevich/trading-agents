"""Portfolio manager pub/sub dual-mode tests — P14.5.

Agent: portfolio_manager
Role: verify the PM subscribes to analysis.recommendations.ready, sizes orders, and
      publishes portfolio.orders.ready via claim-check; existing RPC path unaffected.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.portfolio_manager.tests.helpers import (
    bar,
    recommendation,
    recommendation_set,
    wire_pm,
)
from contracts.portfolio_manager import OrderIntentSet
from kernel import InMemoryGraphStore, InProcessBus, ReadyEvent, claim_check_read

if TYPE_CHECKING:
    from contracts.provider import OHLCVBar


def _bars() -> tuple[OHLCVBar, ...]:
    return (bar("AAPL", 2, close=150.0), bar("AAPL", 0, close=155.0))


def _seed_recommendation_result(
    graph: InMemoryGraphStore,
    *,
    run_id: str = "run-pm-1",
) -> dict[str, object]:
    """Write a RecommendationResult node directly (no publish) and return event dict."""
    rec_set = recommendation_set(recommendation("AAPL", confidence=0.85))
    graph.merge_node(
        "RecommendationResult",
        f"analysis:{run_id}",
        {"recommendations": rec_set.model_dump(mode="json")},
    )
    return ReadyEvent(
        topic="analysis.recommendations.ready",
        label="RecommendationResult",
        ref=f"analysis:{run_id}",
        run_id=run_id,
    ).model_dump(mode="json")


def _wire_with_recs(
    *, run_id: str = "run-pm-1"
) -> tuple[InProcessBus, InMemoryGraphStore, dict[str, object]]:
    bus, graph, _ = wire_pm(source_bars=_bars())
    event = _seed_recommendation_result(graph, run_id=run_id)
    return bus, graph, event


def test_recommendations_ready_triggers_orders_ready() -> None:
    bus, _, event = _wire_with_recs()
    received: list[dict[str, object]] = []
    bus.subscribe("portfolio.orders.ready", received.append)

    bus.publish("analysis.recommendations.ready", event)

    assert len(received) == 1
    assert received[0]["topic"] == "portfolio.orders.ready"
    assert str(received[0]["ref"]).startswith("orders:")


def test_order_intent_result_node_in_graph() -> None:
    bus, graph, event = _wire_with_recs(run_id="run-pm-2")
    received: list[dict[str, object]] = []
    bus.subscribe("portfolio.orders.ready", received.append)

    bus.publish("analysis.recommendations.ready", event)

    node = claim_check_read(graph, received[0])
    assert node.label == "OrderIntentResult"
    assert "orders" in node.props


def test_order_intent_result_is_deserializable() -> None:
    bus, graph, event = _wire_with_recs(run_id="run-pm-3")
    received: list[dict[str, object]] = []
    bus.subscribe("portfolio.orders.ready", received.append)

    bus.publish("analysis.recommendations.ready", event)

    node = claim_check_read(graph, received[0])
    order_set = OrderIntentSet.model_validate(node.props["orders"])
    assert isinstance(order_set, OrderIntentSet)


def test_run_id_propagated_in_orders_ready_event() -> None:
    bus, _, event = _wire_with_recs(run_id="pm-run-99")
    received: list[dict[str, object]] = []
    bus.subscribe("portfolio.orders.ready", received.append)

    bus.publish("analysis.recommendations.ready", event)

    assert received[0]["run_id"] == "pm-run-99"


def test_existing_rpc_evaluate_orders_still_works() -> None:
    from agents.portfolio_manager.tests.helpers import evaluate_message

    bus, _, _ = _wire_with_recs()
    recs = recommendation_set(recommendation("AAPL", confidence=0.85))

    response = bus.request(evaluate_message(recs))

    assert response.message_type == "response"
