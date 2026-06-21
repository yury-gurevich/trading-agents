"""Execution submit core shared by the bus and graph-pull paths.

Agent: execution
Role: submit one approved OrderIntentSet through the idempotent broker port, honour
      the live-stage gate, and persist fills. Called by the bus handler (`_submit`) and
      the graph-pull poll path (`execute_pm_node`) so both stay consistent (DL-08b).
External I/O: injected Broker and GraphStore backends.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.execution.domain.orders import execution_run_id, order_from_intent
from agents.execution.domain.result import execution_result
from agents.execution.domain.submit import remember, submit_order
from agents.execution.live_gate import live_gate_rejected
from agents.execution.store import current_stage_from_graph, write_fills

if TYPE_CHECKING:
    from agents.execution.broker import Broker, BrokerFill
    from contracts.execution import ExecutionResult, ExecutionStage
    from contracts.portfolio_manager import OrderIntentSet
    from kernel import FaultSink, GraphStore


def run_submit(
    graph: GraphStore,
    broker: Broker,
    sink: FaultSink,
    recorded: dict[str, BrokerFill],
    order_set: OrderIntentSet,
    *,
    default_stage: ExecutionStage,
) -> ExecutionResult:
    """Submit an approved order set through the broker and persist fills."""
    stage = current_stage_from_graph(graph, default_stage)
    orders = tuple(
        order_from_intent(order_set, intent) for intent in order_set.approved
    )
    if stage not in ("paper", "broker_shadow"):
        return live_gate_rejected(graph, order_set, orders, stage)
    fills = tuple(submit_order(broker, sink, order, "submit") for order in orders)
    remember(recorded, fills)
    run_id = execution_run_id("submit", order_set.run_id)
    provenance = write_fills(graph, run_id=run_id, fills=fills, order_set=order_set)
    return execution_result(run_id, stage, fills, provenance)
