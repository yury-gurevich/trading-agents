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
from agents.execution.fill_attempts import latest_fill_attempt
from agents.execution.live_gate import live_gate_rejected
from agents.execution.order_tolerance import OrderToleranceConfig
from agents.execution.store import current_stage_from_graph, write_fills
from contracts.broker_lifecycle import is_completed_exit_fill
from contracts.common import Provenance
from kernel import AgentFault, fault_boundary

if TYPE_CHECKING:
    from agents.execution.broker import Broker, BrokerFill
    from agents.execution.domain.orders import BrokerOrder
    from agents.execution.settings import ExecutionSettings
    from contracts.execution import ExecutionResult
    from contracts.portfolio_manager import OrderIntent, OrderIntentSet
    from kernel import FaultSink, GraphStore, Node


def run_submit(
    graph: GraphStore,
    broker: Broker,
    sink: FaultSink,
    recorded: dict[str, BrokerFill],
    order_set: OrderIntentSet,
    *,
    settings: ExecutionSettings,
) -> ExecutionResult:
    """Submit an approved order set through the broker and persist fills."""
    stage = current_stage_from_graph(graph, settings.stage)
    tolerance_config = OrderToleranceConfig.from_settings(settings)
    orders = tuple(
        order_from_intent(order_set, intent, tolerance_config)
        for intent in order_set.approved
    )
    if stage not in ("paper", "broker_shadow"):
        return live_gate_rejected(graph, order_set, orders, stage)
    run_id = execution_run_id("submit", order_set.run_id)
    fills: list[BrokerFill] = []
    skipped = 0
    provenance = _empty_provenance(run_id)
    for intent, order in zip(order_set.approved, orders, strict=True):
        prior_fill = _completed_exit_fill(graph, intent, order)
        if prior_fill is not None:
            skipped += 1
            _record_completed_exit_skip(sink, intent, prior_fill)
            continue
        fill: BrokerFill | None = None
        fill_provenance: Provenance | None = None
        with fault_boundary(
            sink,
            agent="execution",
            module="agents.execution.run",
            capability="submit",
            reraise=False,
        ) as capture:
            fill = submit_order(broker, sink, order, "submit")
            fill_provenance = write_fills(
                graph, run_id=run_id, fills=(fill,), order_set=order_set
            )
        if capture.fault is None and fill is not None and fill_provenance is not None:
            fills.append(fill)
            if provenance.graph_node_id is None:
                provenance = fill_provenance
    submitted = tuple(fills)
    remember(recorded, submitted)
    return execution_result(run_id, stage, submitted, provenance, skipped=skipped)


def _empty_provenance(run_id: str) -> Provenance:
    return Provenance(run_id=run_id, source_agent="execution")


def _completed_exit_fill(
    graph: GraphStore, intent: OrderIntent, order: BrokerOrder
) -> Node | None:
    if intent.action != "sell" or intent.position_ref is None:
        return None
    fill = latest_fill_attempt(graph, order.idempotency_key)
    if fill is None:
        return None
    return fill if is_completed_exit_fill(fill) else None


def _record_completed_exit_skip(
    sink: FaultSink, intent: OrderIntent, prior_fill: Node
) -> None:
    position_ref = intent.position_ref or "unknown"
    sink.submit(
        AgentFault(
            source_agent="execution",
            source_module="agents.execution.run",
            capability="skip_completed_exit",
            severity="warning",
            error_type="CompletedExitReplaySkipped",
            message=(
                f"skipped completed exit for {intent.ticker} "
                f"position_ref={position_ref}; prior_fill_key={prior_fill.key}"
            ),
            context={
                "ticker": intent.ticker,
                "position_ref": position_ref,
                "prior_fill_key": prior_fill.key,
            },
        )
    )
