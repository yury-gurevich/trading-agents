"""Execution graph-poll work source (DL-08 / DL-08b).

Agent: execution
Role: find PMRun nodes execution has not submitted yet and run them straight from the
      graph — reading the PM's OrderIntentSet, submitting through the injected broker,
      writing fills and an ExecutionRun anchor — with no live bus RPC.
External I/O: injected Broker and GraphStore backends.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.execution.run import run_submit
from agents.execution.settings import ExecutionSettings
from contracts.portfolio_manager import OrderIntentSet
from kernel import CollectingFaultSink

if TYPE_CHECKING:
    from agents.execution.broker import Broker
    from kernel import FaultSink, GraphStore, Node

PM_RUN_LABEL = "PMRun"
EXECUTED_EDGE = "EXECUTED_BY"


def find_pending(graph: GraphStore) -> list[Node]:
    """Return PMRun nodes with no downstream ExecutionRun (unprocessed work)."""
    pending: list[Node] = []
    for node in graph.list_nodes(PM_RUN_LABEL):
        executed = list(
            graph.descendants(node, max_depth=1, edge_types={EXECUTED_EDGE})
        )
        if not executed:
            pending.append(node)
    return pending


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
    sink = sink if sink is not None else CollectingFaultSink()
    order_set = OrderIntentSet.model_validate(node.props["order_intent_set"])
    result = run_submit(
        graph, broker, sink, {}, order_set, default_stage=settings.stage
    )
    execution_run = graph.merge_node(
        "ExecutionRun",
        result.run_id,
        {
            "source_pm_run_id": order_set.run_id,
            "submitted": result.submitted,
            "rejected": result.rejected,
        },
    )
    graph.add_edge(node, execution_run, EXECUTED_EDGE)
