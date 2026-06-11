"""Live-stage submission rejection helper.

Agent: execution
Role: reject submissions when the graph-authoritative stage is not paper-safe.
External I/O: GraphStore writes rejected Fill nodes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.execution.domain.orders import execution_run_id, rejected_broker_fill
from agents.execution.domain.result import execution_result
from agents.execution.store import write_fills

if TYPE_CHECKING:
    from agents.execution.domain.orders import BrokerOrder
    from contracts.execution import ExecutionResult, ExecutionStage
    from contracts.portfolio_manager import OrderIntentSet
    from kernel import GraphStore


def live_gate_rejected(
    graph: GraphStore,
    order_set: OrderIntentSet,
    orders: tuple[BrokerOrder, ...],
    stage: ExecutionStage,
) -> ExecutionResult:
    """Record rejected fills instead of submitting in live-adjacent stages."""
    fills = tuple(
        rejected_broker_fill(order, f"stage {stage} requires live broker gating")
        for order in orders
    )
    run_id = execution_run_id("submit", order_set.run_id)
    provenance = write_fills(graph, run_id=run_id, fills=fills, order_set=order_set)
    return execution_result(run_id, stage, fills, provenance)
