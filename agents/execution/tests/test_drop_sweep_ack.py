"""Drop-sweep untracked-order acknowledgement tests for S181.

Agent: execution
Role: prove no-Fill broker orders report once without hiding later Fill repair.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.drop_sweep import sweep_unfilled_orders
from agents.execution.drop_sweep_ack import (
    ACK_LINEAGE_STATUS,
    record_untracked_order_ack,
    untracked_order_ack_key,
)
from agents.execution.tests.broker_stop_helpers import TrackingBroker
from agents.execution.tests.drop_sweep_helpers import broker_order, seed_fill_lineage
from kernel import CollectingFaultSink, GraphFaultSink, InMemoryGraphStore, Node


def test_untracked_ack_record_is_idempotent_when_helper_replays() -> None:
    """EXEC-STA-03 / EXEC-OBS-02: ack evidence is append-safe."""
    graph = InMemoryGraphStore()
    order = broker_order("old-run:LOST:buy", "LOST", status="rejected")
    sink = CollectingFaultSink()

    record_untracked_order_ack(graph, sink, order, "canceled")
    first = graph.get_node("BrokerOrderStatus", untracked_order_ack_key(order))
    record_untracked_order_ack(graph, sink, order, "canceled")
    second = graph.get_node("BrokerOrderStatus", untracked_order_ack_key(order))

    assert first is not None
    assert second == first
    assert len(graph.list_nodes("BrokerOrderStatus")) == 1
    assert len(sink.faults) == 2


def test_untracked_terminal_order_faults_once_across_sweeps() -> None:
    """EXEC-FAIL-01 / EXEC-OBS-02: untracked terminal orders report once."""
    graph = InMemoryGraphStore()
    key = "old-run:LOST:buy"
    broker = TrackingBroker(
        broker_fills=(broker_order(key, "LOST", status="rejected", reason="canceled"),)
    )

    first = sweep_unfilled_orders(
        graph, broker, GraphFaultSink(graph, CollectingFaultSink()), run_id="new-run"
    )
    second = sweep_unfilled_orders(
        graph, broker, GraphFaultSink(graph, CollectingFaultSink()), run_id="new-run"
    )

    faults = _untracked_faults(graph)
    assert (first, second) == (0, 0)
    assert len(faults) == 1
    assert len(graph.list_nodes("BrokerOrderStatus")) == 1
    assert graph.list_nodes("ExecutionRun") == ()


def test_new_untracked_terminal_order_still_faults_on_first_sight() -> None:
    """EXEC-FAIL-01 / EXEC-OBS-02: ack memory is per broker order."""
    graph = InMemoryGraphStore()
    old_key = "old-run:OLD:buy"
    new_key = "old-run:NEW:buy"
    broker = TrackingBroker(
        broker_fills=(
            broker_order(old_key, "OLD", status="rejected", reason="canceled"),
        )
    )

    sweep_unfilled_orders(
        graph, broker, GraphFaultSink(graph, CollectingFaultSink()), run_id="new-run"
    )
    broker.broker_fills = (
        broker_order(old_key, "OLD", status="rejected", reason="canceled"),
        broker_order(new_key, "NEW", status="rejected", reason="canceled"),
    )
    sweep_unfilled_orders(
        graph, broker, GraphFaultSink(graph, CollectingFaultSink()), run_id="new-run"
    )

    faults = _untracked_faults(graph)
    assert len(faults) == 2
    assert {node.props["severity"] for node in faults} == {"error"}
    assert len(graph.list_nodes("BrokerOrderStatus")) == 2


def test_later_fill_takes_precedence_over_untracked_ack() -> None:
    """EXEC-OUT-07 / EXEC-OBS-02: repaired Fill lineage records the drop."""
    graph = InMemoryGraphStore()
    key = "old-run:LOST:buy"
    broker = TrackingBroker(
        broker_fills=(broker_order(key, "LOST", status="rejected", reason="canceled"),)
    )

    first = sweep_unfilled_orders(
        graph, broker, GraphFaultSink(graph, CollectingFaultSink()), run_id="new-run"
    )
    seed_fill_lineage(graph, "old-run", key, "LOST")
    second = sweep_unfilled_orders(
        graph, broker, GraphFaultSink(graph, CollectingFaultSink()), run_id="new-run"
    )

    fill = graph.get_node("Fill", key)
    execution = graph.get_node("ExecutionRun", "execution-submit-old-run")
    statuses = graph.list_nodes("BrokerOrderStatus")
    assert (first, second) == (0, 1)
    assert fill is not None
    assert fill.props["drop_reason"] == "unfilled at session end"
    assert execution is not None
    assert execution.props["dropped"] == 1
    assert len(statuses) == 2
    assert _ack_count(statuses) == 1


def test_fill_lineage_first_does_not_write_untracked_ack() -> None:
    """EXEC-OUT-07 / EXEC-OBS-02: ordinary Fill drops stay ordinary."""
    graph = InMemoryGraphStore()
    key = "old-run:FOUND:buy"
    seed_fill_lineage(graph, "old-run", key, "FOUND")
    broker = TrackingBroker(
        broker_fills=(broker_order(key, "FOUND", status="rejected", reason="canceled"),)
    )

    dropped = sweep_unfilled_orders(
        graph, broker, GraphFaultSink(graph, CollectingFaultSink()), run_id="new-run"
    )

    statuses = graph.list_nodes("BrokerOrderStatus")
    assert dropped == 1
    assert len(statuses) == 1
    assert statuses[0].props.get("lineage_status") is None


def _untracked_faults(graph: InMemoryGraphStore) -> list[Node]:
    return [
        node
        for node in graph.list_nodes("Fault")
        if node.props["error_type"] == "UntrackedOpenOrder"
    ]


def _ack_count(statuses: tuple[Node, ...]) -> int:
    return sum(
        node.props.get("lineage_status") == ACK_LINEAGE_STATUS for node in statuses
    )
