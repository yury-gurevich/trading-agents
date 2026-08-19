"""Drop-sweep edge coverage for ADR-0018 same-session decisions.

Agent: execution
Role: prove stale-order cleanup handles partial broker and graph evidence.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.drop_sweep import sweep_unfilled_orders
from agents.execution.drop_sweep_ack import (
    ACK_LINEAGE_STATUS,
    untracked_order_ack_key,
)
from agents.execution.drop_sweep_records import (
    mark_execution_runs,
    remember_execution_run,
)
from agents.execution.tests.broker_stop_helpers import TrackingBroker
from agents.execution.tests.drop_sweep_helpers import (
    broker_order,
    seed_fill_lineage,
    stop_fact,
)
from kernel import CollectingFaultSink, GraphFaultSink, InMemoryGraphStore


def test_resolved_rejected_order_is_recorded_as_drop_without_cancel() -> None:
    """EXEC-STA-03 / EXEC-OBS-02: resolved broker orders stay query-visible."""
    graph = InMemoryGraphStore()
    expired_key = "old-run:EXP:buy"
    canceled_key = "old-run:CXL:buy"
    seed_fill_lineage(graph, "old-run", expired_key, "EXP")
    seed_fill_lineage(graph, "old-run", canceled_key, "CXL")
    broker = TrackingBroker(
        broker_fills=(
            broker_order(expired_key, "EXP", status="rejected", reason="expired"),
            broker_order(canceled_key, "CXL", status="rejected", reason="canceled"),
        )
    )
    sink = GraphFaultSink(graph, CollectingFaultSink())

    dropped = sweep_unfilled_orders(graph, broker, sink, run_id="new-run")

    expired_fill = graph.get_node("Fill", expired_key)
    canceled_fill = graph.get_node("Fill", canceled_key)
    assert dropped == 2
    assert broker.cancelled == []
    assert expired_fill is not None
    assert canceled_fill is not None
    assert "broker_status" not in expired_fill.props
    assert "broker_status" not in canceled_fill.props
    assert expired_fill.props["drop_reason"] == "unfilled at session end"
    statuses = sorted(
        node.props["status"] for node in graph.list_nodes("BrokerOrderStatus")
    )
    assert statuses == ["canceled", "expired"]


def test_untracked_pipeline_order_is_faulted_after_cancel_attempt() -> None:
    """EXEC-FAIL-01 / EXEC-OBS-02: missing Fill lineage is loud, not silent."""
    graph = InMemoryGraphStore()
    key = "old-run:GHOST:buy"
    broker = TrackingBroker(broker_fills=(broker_order(key, "GHOST"),))
    sink = GraphFaultSink(graph, CollectingFaultSink())

    dropped = sweep_unfilled_orders(graph, broker, sink, run_id="new-run")

    assert dropped == 0
    assert broker.cancelled == [f"broker:{key}"]
    status = graph.list_nodes("BrokerOrderStatus")[0]
    assert status.props["lineage_status"] == ACK_LINEAGE_STATUS
    fault = graph.list_nodes("Fault")[0]
    assert fault.props["error_type"] == "UntrackedOpenOrder"
    assert fault.props["severity"] == "error"


def test_resolved_untracked_order_is_faulted_without_cancel() -> None:
    """EXEC-FAIL-01 / EXEC-OBS-02: unlinked expired orders cannot look green."""
    graph = InMemoryGraphStore()
    key = "old-run:LOST:buy"
    broker = TrackingBroker(
        broker_fills=(broker_order(key, "LOST", status="rejected", reason="expired"),)
    )
    sink = GraphFaultSink(graph, CollectingFaultSink())

    dropped = sweep_unfilled_orders(graph, broker, sink, run_id="new-run")

    assert dropped == 0
    assert broker.cancelled == []
    status = graph.list_nodes("BrokerOrderStatus")[0]
    assert status.key == untracked_order_ack_key(broker.broker_fills[0])
    assert status.props["lineage_status"] == ACK_LINEAGE_STATUS
    fault = graph.list_nodes("Fault")[0]
    assert fault.props["error_type"] == "UntrackedOpenOrder"
    assert fault.props["severity"] == "error"


def test_graph_tracked_stop_mismatch_is_faulted_and_exempted() -> None:
    """EXEC-NEV-01 / EXEC-NEV-03: stop identity mismatch keeps risk protection."""
    graph = InMemoryGraphStore()
    key = "old-run:SAFE:sell"
    stop_fact(graph, key, "SAFE", f"broker:{key}")
    broker = TrackingBroker(
        broker_fills=(broker_order(key, "SAFE", side="sell", order_type="limit"),)
    )
    sink = GraphFaultSink(graph, CollectingFaultSink())

    dropped = sweep_unfilled_orders(graph, broker, sink, run_id="new-run")

    assert dropped == 0
    assert broker.cancelled == []
    assert graph.list_nodes("Fault")[0].props["error_type"] == (
        "BrokerStopIdentityMismatch"
    )


def test_broker_stop_mismatch_is_faulted_and_exempted() -> None:
    """EXEC-NEV-01 / EXEC-NEV-03: broker stop mismatch keeps risk protection."""
    graph = InMemoryGraphStore()
    key = "old-run:SAFE:sell"
    broker = TrackingBroker(
        broker_fills=(broker_order(key, "SAFE", side="sell", order_type="stop_limit"),)
    )
    sink = GraphFaultSink(graph, CollectingFaultSink())

    dropped = sweep_unfilled_orders(graph, broker, sink, run_id="new-run")

    assert dropped == 0
    assert broker.cancelled == []
    assert graph.list_nodes("Fault")[0].props["error_type"] == (
        "BrokerStopIdentityMismatch"
    )


def test_run_marking_helpers_tolerate_missing_lineage_and_existing_count() -> None:
    """EXEC-OBS-02: run-level drop counts are additive evidence only."""
    graph = InMemoryGraphStore()
    touched: set[str] = set()
    remember_execution_run(graph, None, touched)
    fill = graph.merge_node("Fill", "orphan", {})
    remember_execution_run(graph, fill, touched)
    order = graph.merge_node("OrderIntent", "order", {})
    graph.add_edge(fill, order, "EXECUTES")
    remember_execution_run(graph, fill, touched)
    pm_run = graph.merge_node("PMRun", "pm", {})
    graph.add_edge(order, pm_run, "EMITTED_BY")
    remember_execution_run(graph, fill, touched)

    run = graph.merge_node("ExecutionRun", "execution-submit-old-run", {"dropped": 7})
    mark_execution_runs(graph, {"execution-submit-old-run", "missing-run"})

    assert touched == set()
    assert run.props["dropped"] == 7
