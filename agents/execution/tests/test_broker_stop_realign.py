"""A live stop resting away from its decided price is replaced in place (S230).

Agent: execution
Role: prove the replace path, its three guards, and that it settles in one run.
External I/O: none.

The fixture is the 2026-09-25 USB shape: the stop rests at 57.47 (the 5 %
fallback) and the PM decided 4.03 %, a 58.06 stop.
"""

from __future__ import annotations

from agents.execution.tests.stop_realign_helpers import (
    DECIDED_STOP_CENTS,
    DECIDED_STOP_PCT,
    RecordingPaperBroker,
    live_stop_count,
    run_placement,
    seed_usb,
    seed_usb_stop,
)
from contracts.broker_stops import active_broker_stop_orders
from kernel import InMemoryGraphStore


def test_a_mismatched_new_stop_is_replaced_in_place() -> None:
    """EXEC-OBS-06 / EXEC-OBS-03: A6 - one replace, markers, no cancel, never bare."""
    graph = InMemoryGraphStore()
    broker = RecordingPaperBroker()
    seed_usb(graph)
    old_key = seed_usb_stop(graph, broker)
    old_id = f"paper:{old_key}"

    sink = run_placement(graph, broker)

    assert broker.replace_calls == [(old_id, DECIDED_STOP_CENTS)]
    assert broker.cancelled == []
    assert broker.live_at_replace == [1]
    assert live_stop_count(broker) == 1
    new_key = f"{old_key}#1"
    old = graph.get_node("BrokerStopOrder", old_key)
    assert old is not None
    assert old.props["replaced_by"] == new_key
    assert old.props["replaced_at"]
    assert [
        (stop.key, stop.stop_price_cents) for stop in active_broker_stop_orders(graph)
    ] == [(new_key, DECIDED_STOP_CENTS)]
    new = graph.get_node("BrokerStopOrder", new_key)
    assert new is not None
    assert new.props["replaces"] == old_key
    assert new.props["stop_pct"] == DECIDED_STOP_PCT
    assert new.props["stop_pct_source"] == "lineage"
    assert new.props["derived_from"] == "active_position"
    assert new.props["broker_order_id"] == f"paper:{new_key}"
    assert sink.faults == []


def test_an_accepted_stop_is_not_replaced() -> None:
    """EXEC-OBS-06: A7 - Alpaca refuses to replace an accepted order; never ask."""
    graph = InMemoryGraphStore()
    broker = RecordingPaperBroker(stop_order_status="accepted")
    seed_usb(graph)
    old_key = seed_usb_stop(graph, broker)

    sink = run_placement(graph, broker)

    assert broker.replace_calls == []
    assert [stop.key for stop in active_broker_stop_orders(graph)] == [old_key]
    assert [fault.error_type for fault in sink.faults] == ["StopReplaceSkipped"]
    assert sink.faults[0].context["order_status"] == "accepted"
    assert sink.faults[0].severity == "warning"


def test_a_stop_is_never_moved_to_or_above_the_market() -> None:
    """EXEC-OBS-06: A8 - a breached decided width is the operator's call, not ours."""
    graph = InMemoryGraphStore()
    broker = RecordingPaperBroker()
    seed_usb(graph)
    old_key = seed_usb_stop(graph, broker)

    sink = run_placement(graph, broker, price_cents=5800)

    assert broker.replace_calls == []
    assert [stop.key for stop in active_broker_stop_orders(graph)] == [old_key]
    assert [fault.error_type for fault in sink.faults] == ["StopReplaceRefused"]
    fault = sink.faults[0]
    assert fault.severity == "warning"
    assert "USB" in fault.message
    assert "58.06" in fault.message
    assert "58.00" in fault.message


def test_a_failed_replace_keeps_the_old_stop_and_retries() -> None:
    """EXEC-OBS-06 / EXEC-OBS-03: A9 - a failure leaves the stop live and unmarked."""
    graph = InMemoryGraphStore()
    broker = RecordingPaperBroker(fail_replace=True)
    seed_usb(graph)
    old_key = seed_usb_stop(graph, broker)

    first = run_placement(graph, broker)
    broker.fail_replace = False
    second = run_placement(graph, broker)

    assert [fault.error_type for fault in first.faults] == ["StopReplaceFailed"]
    assert "paper replace failed" in first.faults[0].message
    assert len(broker.replace_calls) == 2
    old = graph.get_node("BrokerStopOrder", old_key)
    assert old is not None
    assert old.props["replaced_by"] == f"{old_key}#1"
    assert second.faults == []


def test_a_failed_replace_leaves_no_marker() -> None:
    """EXEC-OBS-06 / EXEC-OBS-03: A9 - the old fact is untouched after a failure."""
    graph = InMemoryGraphStore()
    broker = RecordingPaperBroker(fail_replace=True)
    seed_usb(graph)
    old_key = seed_usb_stop(graph, broker)

    run_placement(graph, broker)

    old = graph.get_node("BrokerStopOrder", old_key)
    assert old is not None
    assert "replaced_at" not in old.props
    assert [stop.key for stop in active_broker_stop_orders(graph)] == [old_key]
    assert live_stop_count(broker) == 1


def test_a_matching_stop_is_left_alone() -> None:
    """EXEC-OBS-06: A11 - a stop already at the decided price draws no broker call."""
    graph = InMemoryGraphStore()
    broker = RecordingPaperBroker()
    seed_usb(graph)
    seed_usb_stop(graph, broker, stop_pct=DECIDED_STOP_PCT)
    orders_before = broker.order_count

    sink = run_placement(graph, broker)

    assert broker.replace_calls == []
    assert broker.fills_reads == 0
    assert broker.order_count == orders_before
    assert sink.faults == []


def test_replacement_is_idempotent_across_runs() -> None:
    """EXEC-OBS-06: A12 - the recomputed price never flutters, so one replace total."""
    graph = InMemoryGraphStore()
    broker = RecordingPaperBroker()
    seed_usb(graph)
    seed_usb_stop(graph, broker)

    run_placement(graph, broker)
    run_placement(graph, broker)

    assert len(broker.replace_calls) == 1
    assert len(active_broker_stop_orders(graph)) == 1
