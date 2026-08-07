"""Exit-path resting-stop settlement, through the real run path (DL-95).

Agent: execution
Role: prove an exit cancels its own stop before submitting, and that a failed
      exit leaves its position loudly unprotected.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.poll import execute_pm_node
from agents.execution.tests.broker_stop_helpers import order_set, seed_pm_run, sell
from agents.execution.tests.exit_stop_helpers import EventBroker, held, resting_stop
from contracts.broker_stops import active_broker_stop_refs
from kernel import CollectingFaultSink, InMemoryGraphStore


def test_exit_cancels_its_stop_before_submitting() -> None:
    """EXEC-DEP-04 / EXEC-IDN-03: the 2026-08-07 case - a resting stop reserves
    the position's shares, so the exit must cancel it before submitting."""
    graph = InMemoryGraphStore()
    broker = EventBroker()
    sink = CollectingFaultSink()
    ref = held(graph, "ABT", 191)
    resting_stop(graph, "ABT", ref)
    node = seed_pm_run(graph, order_set("pm-exit", sell("ABT", 191, ref)))

    execute_pm_node(node, graph=graph, broker=broker, sink=sink)

    assert broker.events == [
        ("cancel", f"broker:stop:{ref}:ABT"),
        ("submit", "ABT"),
    ], "the cancel must precede the submit, not merely also happen"
    assert active_broker_stop_refs(graph) == frozenset()


def test_rejected_exit_leaves_position_loudly_unprotected() -> None:
    """EXEC-OBS-03: a held position ending the run with no live stop is
    surfaced as an UnprotectedPosition fault, never silently unprotected."""
    graph = InMemoryGraphStore()
    broker = EventBroker(reject_sells=True)
    sink = CollectingFaultSink()
    ref = held(graph, "ABT", 191)
    resting_stop(graph, "ABT", ref)
    node = seed_pm_run(graph, order_set("pm-reject", sell("ABT", 191, ref)))

    execute_pm_node(node, graph=graph, broker=broker, sink=sink)

    unprotected = [
        fault for fault in sink.faults if fault.error_type == "UnprotectedPosition"
    ]
    assert len(unprotected) == 1
    assert unprotected[0].context["ticker"] == "ABT"
    assert "stop was cancelled" in unprotected[0].message
