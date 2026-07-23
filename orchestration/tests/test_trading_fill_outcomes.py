"""Fill-outcome classification tests — broker evidence over submit-time status.

Agent: orchestration
Role: prove each broker status lands in the right bucket, and that a later broker
      read overrides what execution recorded when it submitted.
External I/O: none.
"""

from __future__ import annotations

from kernel import InMemoryGraphStore, Node
from orchestration.packs.trading_fill_outcomes import execution_view, fill_outcomes


def _run(graph: InMemoryGraphStore, fills: dict[str, dict[str, object]]) -> Node:
    """Build a PMRun → OrderIntent → Fill shape plus the ExecutionRun that ran it."""
    pm_run = graph.merge_node("PMRun", "pm-run-1", {"approved_count": len(fills)})
    execution_run = graph.merge_node(
        "ExecutionRun", "exec-run-1", {"submitted": len(fills)}
    )
    graph.add_edge(pm_run, execution_run, "EXECUTED_BY")
    for ticker, props in fills.items():
        order = graph.merge_node(
            "OrderIntent",
            f"pm-run-1:{ticker}",
            {"ticker": ticker, "action": "buy"},
        )
        graph.add_edge(order, pm_run, "EMITTED_BY")
        graph.merge_node("Fill", f"pm-run-1:{ticker}:buy", props)
    return execution_run


def test_each_broker_status_lands_in_its_bucket() -> None:
    graph = InMemoryGraphStore()
    run = _run(
        graph,
        {
            "AAPL": {"status": "filled"},
            "MSFT": {"status": "partial"},
            "NVDA": {"status": "rejected"},
            "AMZN": {"status": "canceled"},
            "TSLA": {"status": "pending"},
        },
    )

    outcomes = fill_outcomes(graph, run)

    assert (outcomes.filled, outcomes.unfilled, outcomes.unresolved) == (2, 2, 1)
    assert outcomes.submitted == 5


def test_broker_evidence_overrides_the_submit_time_status() -> None:
    """The 07-21 shape: recorded pending at submit, rejected by the broker later."""
    graph = InMemoryGraphStore()
    run = _run(
        graph,
        {"AAPL": {"status": "pending", "broker_status": "rejected"}},
    )

    outcomes = fill_outcomes(graph, run)

    assert (outcomes.filled, outcomes.unfilled, outcomes.unresolved) == (0, 1, 0)
    assert outcomes.statuses == ("rejected",)


def test_a_run_with_no_orders_reports_nothing_to_resolve() -> None:
    graph = InMemoryGraphStore()
    run = _run(graph, {})

    outcomes = fill_outcomes(graph, run)

    assert outcomes.submitted == 0
    assert outcomes.statuses == ()


def test_execution_view_exposes_the_outcome_to_the_gate() -> None:
    graph = InMemoryGraphStore()
    run = _run(graph, {"AAPL": {"status": "rejected"}, "MSFT": {"status": "filled"}})

    view = execution_view(graph, run)

    assert view.observed["orders"] == 2
    assert view.observed["filled"] == 1
    assert view.observed["unfilled"] == 1
    assert view.observed["statuses"] == "filled, rejected"
    assert any("outcome" in line for line in view.outputs)


def test_an_execution_run_with_no_pm_lineage_has_no_fills() -> None:
    graph = InMemoryGraphStore()
    orphan = graph.merge_node("ExecutionRun", "exec-orphan", {"submitted": 0})

    assert fill_outcomes(graph, orphan).submitted == 0


def test_an_order_with_no_fill_node_is_not_counted() -> None:
    """An intent the broker never received leaves no Fill; it is not an outcome."""
    graph = InMemoryGraphStore()
    run = _run(graph, {"AAPL": {"status": "filled"}})
    stray = graph.merge_node(
        "OrderIntent", "pm-run-1:MSFT", {"ticker": "MSFT", "action": "buy"}
    )
    graph.add_edge(stray, graph.merge_node("PMRun", "pm-run-1", {}), "EMITTED_BY")

    outcomes = fill_outcomes(graph, run)

    assert outcomes.submitted == 1
    assert outcomes.filled == 1
