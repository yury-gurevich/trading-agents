"""Execution broker-stop replacement graph-pull tests.

Agent: execution
Role: prove a cancelled stop from a rejected exit is replaced on a later run.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal

from agents.execution.poll import execute_pm_node
from agents.execution.tests.broker_stop_helpers import order_set, seed_pm_run, sell
from agents.execution.tests.exit_stop_helpers import EventBroker, held, resting_stop
from contracts.broker_stops import (
    BROKER_STOP_ORDER_LABEL,
    active_broker_stop_refs,
)
from contracts.common import Money
from kernel import CollectingFaultSink, InMemoryGraphStore


def test_rejected_exit_reprotects_on_later_hold_run() -> None:
    """EXEC-OBS-03 / EXEC-DEP-04: a cancelled exit stop is retried next run."""
    graph = InMemoryGraphStore()
    broker = EventBroker(reject_sells=True)
    sink = CollectingFaultSink()
    broker.submit("seed:AAPL", "AAPL", "buy", 4, Money(amount=Decimal("100.00")))
    ref = held(graph, "AAPL", 4)
    base_key = resting_stop(graph, "AAPL", ref)

    execute_pm_node(
        seed_pm_run(graph, order_set("pm-exit", sell("AAPL", 4, ref))),
        graph=graph,
        broker=broker,
        sink=sink,
    )
    fault_count = _unprotected_fault_count(sink)
    assert fault_count == 1
    assert active_broker_stop_refs(graph) == frozenset()

    execute_pm_node(
        seed_pm_run(graph, order_set("pm-hold")),
        graph=graph,
        broker=broker,
        sink=sink,
    )

    replacement_key = f"{base_key}#1"
    replacement = graph.get_node(BROKER_STOP_ORDER_LABEL, replacement_key)
    assert replacement is not None
    assert "cancelled_at" not in replacement.props
    assert active_broker_stop_refs(graph) == frozenset({ref})
    assert replacement_key in {fill.idempotency_key for fill in broker.fills()}
    assert _unprotected_fault_count(sink) == fault_count


def _unprotected_fault_count(sink: CollectingFaultSink) -> int:
    return sum(1 for fault in sink.faults if fault.error_type == "UnprotectedPosition")
