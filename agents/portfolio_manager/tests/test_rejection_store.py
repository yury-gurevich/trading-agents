"""Portfolio Manager rejection-store regression tests.

Agent: portfolio_manager
Role: verify durable rejection evidence remains queryable.
External I/O: none.
"""

from __future__ import annotations

from agents.portfolio_manager.store import write_order_decision
from agents.portfolio_manager.tests.helpers import recommendation, recommendation_set
from contracts.portfolio_manager import GateOutcome, RejectedOrder
from kernel import InMemoryGraphStore


def test_store_writes_queryable_rejection_gate_report() -> None:
    """Covers PM-OUT-03 / PM-OBS-01: rejected nodes keep gate evidence."""
    graph = InMemoryGraphStore()
    payload = recommendation_set(recommendation("AAPL"))
    graph.merge_node("AnalystRun", payload.run_id, {"recommendation_count": 1})
    graph.merge_node("Recommendation", f"{payload.run_id}:AAPL", {"ticker": "AAPL"})

    provenance = write_order_decision(
        graph,
        recommendation_set=payload,
        approved=(),
        rejected=(
            RejectedOrder(
                ticker="AAPL",
                reason="max_positions",
                gate_report=(
                    GateOutcome(
                        name="max_positions",
                        value=11.0,
                        threshold=10.0,
                        passed=False,
                        detail="fixture",
                    ),
                ),
            ),
        ),
    )

    rejection = graph.get_node("Rejection", f"{provenance.run_id}:AAPL")
    pm_run = graph.get_node("PMRun", provenance.run_id)
    assert rejection is not None
    assert pm_run is not None
    assert pm_run.props["approved_count"] == 0
    assert pm_run.props["rejected_count"] == 1
    assert pm_run.props["source_analyst_run_id"] == payload.run_id
    assert rejection.props["reason"] == "max_positions"
    assert rejection.props["gate_report"][0]["name"] == "max_positions"
    assert [node.label for node in graph.descendants(rejection, max_depth=1)] == [
        "PMRun",
        "Recommendation",
    ]
