"""Execution graph-poll find_pending + execute_pm_node tests.

Agent: execution
Role: verify execution finds unexecuted PMRun nodes, submits their OrderIntentSet from
      the graph, writes fills, and anchors an ExecutionRun so it is not re-executed.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import agents.execution.run as execution_run
from agents.execution.broker import BrokerFill
from agents.execution.paper_broker import PaperBroker
from agents.execution.poll import execute_pm_node, find_pending
from agents.execution.store import write_fills as store_write_fills
from agents.execution.tests.helpers import order, order_set
from kernel import CollectingFaultSink, GraphFaultSink, InMemoryGraphStore
from kernel.work_loop import run_once

if TYPE_CHECKING:
    import pytest

    from agents.execution.broker import BrokerPosition
    from contracts.common import Money, Provenance
    from contracts.portfolio_manager import OrderIntentSet
    from kernel import GraphStore, Node


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


def test_run_once_continues_after_poisoned_intent_and_anchors_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DRIFT-014 / DL-70 / S145 item 3: planted write raise costs one intent."""
    graph = InMemoryGraphStore()
    payload = order_set(order("AAA"), order("BAD"), order("CCC"))
    _seed_pm_run(graph, payload)
    broker = RecordingBroker()
    inner = CollectingFaultSink()
    sink = GraphFaultSink(graph, inner)

    def poison_middle_write(
        graph_arg: GraphStore,
        *,
        run_id: str,
        fills: tuple[BrokerFill, ...],
        order_set: OrderIntentSet | None = None,
    ) -> Provenance:
        if fills[0].ticker == "BAD":
            raise RuntimeError("poisoned write")
        return store_write_fills(
            graph_arg, run_id=run_id, fills=fills, order_set=order_set
        )

    monkeypatch.setattr(execution_run, "write_fills", poison_middle_write)

    processed = run_once(
        lambda: find_pending(graph),
        lambda item: execute_pm_node(item, graph=graph, broker=broker, sink=sink),
    )

    execution_node = graph.list_nodes("ExecutionRun")[0]
    statuses = {
        node.props["ticker"]: node.props["status"] for node in graph.list_nodes("Fill")
    }
    assert processed.advanced == 1
    assert broker.submitted == [
        "pm-run-fixture:AAA:buy",
        "pm-run-fixture:BAD:buy",
        "pm-run-fixture:CCC:buy",
    ]
    assert execution_node.props["submitted"] == 2
    assert execution_node.props["rejected"] == 0
    assert execution_node.props["skipped"] == 0
    assert statuses == {"AAA": "filled", "CCC": "filled"}
    assert len(graph.list_nodes("Fault")) == 1
    assert find_pending(graph) == []


class RecordingBroker:
    """Broker fake that records every market submission."""

    def __init__(self) -> None:
        self.submitted: list[str] = []

    def submit(
        self,
        idempotency_key: str,
        ticker: str,
        side: Literal["buy", "sell"],
        quantity: int,
        limit_price: Money,
        tolerance_bps: int | None = None,
    ) -> BrokerFill:
        self.submitted.append(idempotency_key)
        return BrokerFill(
            idempotency_key=idempotency_key,
            ticker=ticker,
            side=side,
            quantity=quantity,
            price=limit_price,
            broker_order_id=f"paper:{idempotency_key}",
            status="filled",
        )

    def submit_stop(
        self,
        idempotency_key: str,
        ticker: str,
        side: Literal["buy", "sell"],
        quantity: int,
        stop_price: Money,
        tif: str = "gtc",
    ) -> BrokerFill:
        raise AssertionError("test broker should not submit stops")

    def cancel(self, broker_order_id: str) -> None:
        raise AssertionError("test broker should not cancel stops")

    def fills(self) -> tuple[BrokerFill, ...]:
        return ()

    def positions(self) -> tuple[BrokerPosition, ...]:
        return ()
