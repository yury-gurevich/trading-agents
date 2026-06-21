"""Execution graph-poll find_pending + execute_pm_node tests.

Agent: execution
Role: verify execution finds unexecuted PMRun nodes, submits their OrderIntentSet from
      the graph, writes fills, and anchors an ExecutionRun so it is not re-executed.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.execution.broker import PaperBroker
from agents.execution.poll import execute_pm_node, find_pending
from agents.execution.tests.helpers import order, order_set
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from contracts.portfolio_manager import OrderIntentSet
    from kernel import Node


def _seed_pm_run(graph: InMemoryGraphStore, payload: OrderIntentSet) -> Node:
    return graph.merge_node(
        "PMRun",
        payload.run_id,
        {"order_intent_set": payload.model_dump(mode="json")},
    )


def test_find_pending_returns_unexecuted_pm_run() -> None:
    graph = InMemoryGraphStore()
    _seed_pm_run(graph, order_set(order("AAPL")))
    assert len(find_pending(graph)) == 1


def test_find_pending_empty_when_no_pm_run() -> None:
    assert find_pending(InMemoryGraphStore()) == []


def test_execute_pm_node_submits_and_anchors() -> None:
    graph = InMemoryGraphStore()
    node = _seed_pm_run(graph, order_set(order("AAPL")))
    execute_pm_node(node, graph=graph, broker=PaperBroker())
    assert len(graph.list_nodes("Fill")) == 1
    assert len(graph.list_nodes("ExecutionRun")) == 1
    assert find_pending(graph) == []


def test_execute_pm_node_empty_orders_still_anchors() -> None:
    graph = InMemoryGraphStore()
    node = _seed_pm_run(graph, order_set())
    execute_pm_node(node, graph=graph, broker=PaperBroker())
    assert not graph.list_nodes("Fill")
    assert len(graph.list_nodes("ExecutionRun")) == 1
    assert find_pending(graph) == []
