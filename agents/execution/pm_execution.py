"""Execution of one graph-pulled PMRun.

Agent: execution
Role: submit a PMRun from graph state and anchor the ExecutionRun result.
External I/O: injected Broker and GraphStore backends.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from agents.execution.deliberation_faults import (
    record_failed_open_submit,
    record_unvetoed_submit,
)
from agents.execution.deliberation_gate import (
    deliberation_status,
    drop_vetoed,
    failed_open_tickers,
)
from agents.execution.exit_stops import report_unprotected_exits, settle_stops
from agents.execution.reconciliation import reconcile_run_start
from agents.execution.run import run_submit
from agents.execution.settings import ExecutionSettings
from contracts.portfolio_manager import OrderIntentSet
from kernel import CollectingFaultSink
from kernel.fault_graph import GraphFaultSink

if TYPE_CHECKING:
    from agents.execution.broker import Broker
    from kernel import FaultSink, GraphStore, Node

EXECUTED_EDGE = "EXECUTED_BY"


def execute_pm_node(
    node: Node,
    *,
    graph: GraphStore,
    broker: Broker,
    settings: ExecutionSettings | None = None,
    sink: FaultSink | None = None,
) -> None:
    """Submit one PMRun's orders from the graph and link the ExecutionRun back to it."""
    settings = settings or ExecutionSettings()
    sink = sink if sink is not None else GraphFaultSink(graph, CollectingFaultSink())
    order_set = OrderIntentSet.model_validate(node.props["order_intent_set"])
    status = deliberation_status(
        graph,
        node,
        order_set,
        now=datetime.now(tz=UTC),
        grace_seconds=settings.deliberation_grace_seconds,
    )
    failed_open = failed_open_tickers(graph, node)
    order_set = drop_vetoed(graph, node, order_set)
    snapshot = reconcile_run_start(graph, broker, sink, run_id=order_set.run_id)
    freed = settle_stops(
        graph,
        broker,
        sink,
        order_set,
        snapshot,
        fallback_stop_pct=settings.broker_stop_fallback_stop_pct,
    )
    result = run_submit(graph, broker, sink, {}, order_set, settings=settings)
    report_unprotected_exits(sink, result, freed)
    execution_run = graph.merge_node(
        "ExecutionRun",
        result.run_id,
        {
            "source_pm_run_id": order_set.run_id,
            "submitted": result.submitted,
            "rejected": result.rejected,
            "skipped": result.skipped,
            "deliberation_status": status,
        },
    )
    if status == "proceeded_unvetoed":
        record_unvetoed_submit(sink, order_set.run_id, result.submitted, settings)
    if status == "applied_failed_open":
        record_failed_open_submit(sink, order_set.run_id, result.submitted, failed_open)
    graph.add_edge(node, execution_run, EXECUTED_EDGE)
