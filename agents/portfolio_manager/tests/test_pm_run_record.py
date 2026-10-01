"""What a PM run records: its OrderIntentSet, and no portfolio snapshot (S251, DL-260).

Agent: portfolio_manager
Role: pin the narrowed DRIFT-039 clauses: the graph-pull PMRun carries the run's whole
      OrderIntentSet as order_intent_set and the pub/sub OrderIntentResult carries the
      same set as orders; neither records a pre- or post-run portfolio state.
External I/O: none (in-memory graph).
"""

from __future__ import annotations

from agents.portfolio_manager.poll import evaluate_analyst_node
from agents.portfolio_manager.tests.test_pm_poll import _seed_analyst_run, _settings
from contracts.portfolio_manager import OrderIntentSet
from kernel import InMemoryGraphStore

_SET_FIELDS = {"run_id", "approved", "rejected", "explanation", "provenance"}
_RUN_PROPS = {
    "order_intent_set",
    "approved_count",
    "rejected_count",
    "source_analyst_run_id",
    "created_at",
}


def test_a_pm_run_carries_its_order_intent_set_and_no_portfolio_snapshot() -> None:
    """PM-STA-04 / PM-OBS-01 (DRIFT-039): the graph-pull PMRun holds the run's final
    OrderIntentSet - each approved intent with its estimated price and gate_report -
    under order_intent_set, beside its counts, source AnalystRun and creation time,
    and holds no portfolio-state snapshot of any kind."""
    graph = InMemoryGraphStore()
    evaluate_analyst_node(_seed_analyst_run(graph), graph=graph, settings=_settings())

    [pm_run] = graph.list_nodes("PMRun")
    recorded = pm_run.props["order_intent_set"]
    order_set = OrderIntentSet.model_validate(recorded)

    assert set(pm_run.props) == _RUN_PROPS
    assert set(recorded) == _SET_FIELDS
    assert [(i.ticker, i.est_price.amount > 0) for i in order_set.approved] == [
        ("AAPL", True)
    ]
    assert order_set.approved[0].gate_report
    assert "snapshot" not in str(pm_run.props)
