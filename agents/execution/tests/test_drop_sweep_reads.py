"""A1-A5: a head-of-run sweep reads each graph label once (S279).

Agent: execution
Role: prove read bounds, drop equivalence and contained graph-read failures.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.label_reads_support import LabelReadCounter, seed_sweep

from agents.execution.drop_sweep import sweep_unfilled_orders
from agents.execution.poll import sync_run_request
from agents.execution.tests.broker_stop_helpers import TrackingBroker
from agents.execution.tests.drop_sweep_helpers import broker_order, seed_fill_lineage
from kernel import CollectingFaultSink

if TYPE_CHECKING:
    from kernel import Node


def test_a1_one_sweep_reads_each_label_once() -> None:
    """EXEC-PERF-02 / EXEC-OUT-07: only the stale limit is cancelled and dropped."""
    graph = LabelReadCounter()
    broker = seed_sweep(graph)
    sink = CollectingFaultSink()

    dropped = sweep_unfilled_orders(graph, broker, sink, run_id="new-run")

    assert dropped == 1
    assert broker.cancelled == ["broker:old-run:AAA:buy"]
    fill = graph.get_node("Fill", "old-run:AAA:buy")
    assert fill is not None
    assert fill.props["drop_reason"] == "unfilled at session end"
    assert fill.props["dropped_at"]
    assert "broker_status" not in fill.props
    statuses = graph.list_nodes("BrokerOrderStatus")
    assert len(statuses) == 1
    assert statuses[0].props["status"] == "canceled"
    assert [fault.error_type for fault in sink.faults] == ["DroppedDecision"]
    assert graph.listed["Fill"] == 1
    assert graph.listed["BrokerStopOrder"] == 1


def test_a2_the_run_start_reads_fill_twice_whatever_the_orders() -> None:
    """EXEC-PERF-02 / EXEC-TRG-07: the sweep and refresh each read Fill once."""
    graph = LabelReadCounter()
    broker = seed_sweep(graph)
    request = graph.merge_node("RunRequest", "new-run", {"run_id": "new-run"})

    sync_run_request(request, graph=graph, broker=broker, sink=CollectingFaultSink())

    assert len(graph.list_nodes("BrokerPositionSnapshot")) == 1
    assert broker.cancelled == ["broker:old-run:AAA:buy"]
    assert graph.listed["Fill"] == 2
    assert graph.listed["BrokerStopOrder"] == 1


def test_a3_a_drop_in_the_sweep_is_seen_by_a_later_order() -> None:
    """EXEC-PERF-02 / EXEC-IDM-02: rejected K drops K#1 before K#1 is visited."""
    graph = LabelReadCounter()
    key = "old-run:AAA:buy"
    seed_fill_lineage(graph, "old-run", key, "AAA")
    first = graph.get_node("Fill", key)
    assert first is not None
    attempt = graph.merge_node(
        "Fill",
        f"{key}#1",
        {**first.props, "attempt_ordinal": 1, "broker_order_id": f"broker:{key}#1"},
    )
    order = graph.get_node("OrderIntent", "old-run:AAA")
    assert order is not None
    graph.add_edge(attempt, order, "EXECUTES")
    broker = TrackingBroker(
        broker_fills=(
            broker_order(key, "AAA", status="rejected", reason="expired"),
            broker_order(f"{key}#1", "AAA"),
        )
    )

    dropped = sweep_unfilled_orders(
        graph, broker, CollectingFaultSink(), run_id="new-run"
    )

    assert dropped == 1
    assert broker.cancelled == []
    statuses = graph.list_nodes("BrokerOrderStatus")
    assert len(statuses) == 1
    assert statuses[0].props["fill_key"] == f"{key}#1"
    assert statuses[0].props["status"] == "expired"


def test_a4_no_broker_order_reads_no_label() -> None:
    """EXEC-PERF-02: no broker orders means no graph label is listed."""
    graph = LabelReadCounter()

    assert (
        sweep_unfilled_orders(
            graph, TrackingBroker(), CollectingFaultSink(), run_id="new-run"
        )
        == 0
    )
    assert not graph.listed


def test_a5_a_failed_read_is_one_fault_and_no_cancel() -> None:
    """EXEC-PERF-02 / EXEC-FAIL-02: two orders share one contained read failure."""

    class FailedReads(LabelReadCounter):
        def list_nodes(self, label: str) -> tuple[Node, ...]:
            if label == "Fill":
                raise RuntimeError("Fill label unavailable")
            return super().list_nodes(label)

    graph = FailedReads()
    broker = TrackingBroker(
        broker_fills=(
            broker_order("old-run:AAA:buy", "AAA"),
            broker_order("old-run:BBB:buy", "BBB"),
        )
    )
    sink = CollectingFaultSink()

    assert sweep_unfilled_orders(graph, broker, sink, run_id="new-run") == 0
    assert broker.cancelled == []
    assert len(sink.faults) == 1
    assert sink.faults[0].capability == "drop_unfilled_orders"
    assert sink.faults[0].error_type == "RuntimeError"
