"""Execution graph-poll work source (DL-08 / DL-08b).

Agent: execution
Role: find PMRun nodes execution has not submitted yet and run them straight from the
      graph — reading the PM's OrderIntentSet, submitting through the injected broker,
      writing fills and an ExecutionRun anchor — with no live bus RPC.
External I/O: injected Broker and GraphStore backends.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

from agents.execution.deliberation_gate import is_waiting
from agents.execution.drop_sweep import sweep_unfilled_orders
from agents.execution.pm_execution import EXECUTED_EDGE as EXECUTED_EDGE
from agents.execution.pm_execution import execute_pm_node as execute_pm_node
from agents.execution.reconciliation import reconcile_run_start
from agents.execution.settings import ExecutionSettings
from contracts.position_sync import (
    RUN_REQUEST_LABEL,
    SNAPSHOT_REFRESH_EDGE,
    linked_snapshot,
    run_request_id,
)
from kernel import CollectingFaultSink, fault_boundary
from kernel.fault_graph import GraphFaultSink

if TYPE_CHECKING:
    from agents.execution.broker import Broker
    from kernel import FaultSink, GraphStore, Node

PM_RUN_LABEL = "PMRun"


@dataclass(frozen=True)
class ExecutionWorkItem:
    """One execution poll item, preserving a single work_loop entrypoint."""

    kind: Literal["position_sync", "submit"]
    node: Node


def find_pending_position_sync(graph: GraphStore) -> list[Node]:
    """Return RunRequest nodes with no execution-authored broker snapshot."""
    pending: list[Node] = []
    for node in graph.list_nodes(RUN_REQUEST_LABEL):
        if linked_snapshot(graph, node) is None:
            pending.append(node)
    return pending


def find_pending(
    graph: GraphStore, *, settings: ExecutionSettings | None = None
) -> list[Node]:
    """Return PMRun nodes ready to submit: unexecuted, and not awaiting a veto.

    A buy-carrying PMRun stays *unconsumed* while its grace window is open, so the
    next poll retries it — no new state, and a restart resumes correctly because the
    window is measured from the PMRun's own `created_at` (DL-98).
    """
    active = settings or ExecutionSettings()
    now = datetime.now(tz=UTC)
    pending: list[Node] = []
    for node in graph.list_nodes(PM_RUN_LABEL):
        executed = list(
            graph.descendants(node, max_depth=1, edge_types={EXECUTED_EDGE})
        )
        if executed:
            continue
        if is_waiting(graph, node, now=now, settings=active):
            continue
        pending.append(node)
    return pending


def find_pending_work(graph: GraphStore) -> list[ExecutionWorkItem]:
    """Return head sync work before order-submission work."""
    return [
        *(
            ExecutionWorkItem("position_sync", node)
            for node in find_pending_position_sync(graph)
        ),
        *(ExecutionWorkItem("submit", node) for node in find_pending(graph)),
    ]


def process_work_item(
    item: ExecutionWorkItem,
    *,
    graph: GraphStore,
    broker: Broker,
    settings: ExecutionSettings | None = None,
    sink: FaultSink | None = None,
) -> None:
    """Dispatch one execution work item without widening the work_loop."""
    if item.kind == "position_sync":
        sync_run_request(item.node, graph=graph, broker=broker, sink=sink)
    else:
        execute_pm_node(
            item.node, graph=graph, broker=broker, settings=settings, sink=sink
        )


def sync_run_request(
    node: Node,
    *,
    graph: GraphStore,
    broker: Broker,
    sink: FaultSink | None = None,
) -> None:
    """Write a run-start broker snapshot and link it to its RunRequest."""
    sink = sink if sink is not None else GraphFaultSink(graph, CollectingFaultSink())
    run_id = run_request_id(node)
    with fault_boundary(
        sink,
        agent="execution",
        module="agents.execution.poll",
        capability="drop_unfilled_orders",
        reraise=False,
    ):
        sweep_unfilled_orders(graph, broker, sink, run_id=run_id)
    with fault_boundary(
        sink,
        agent="execution",
        module="agents.execution.poll",
        capability="position_sync",
        reraise=False,
    ) as capture:
        snapshot = reconcile_run_start(graph, broker, sink, run_id=run_id)
        if snapshot is not None:
            graph.add_edge(node, snapshot, SNAPSHOT_REFRESH_EDGE)
    if capture.fault is not None:
        return
