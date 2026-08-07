"""Exit-path stop cancellation, unit level (DL-95).

Agent: execution
Role: prove which stops are freed, that cancellation is an appended marker, and
      that the unprotected report only speaks for positions actually freed.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal

from agents.execution.exit_stops import cancel_stops_for_exits, report_unprotected_exits
from agents.execution.tests.broker_stop_helpers import order_set, sell
from agents.execution.tests.exit_stop_helpers import EventBroker, held, resting_stop
from contracts.broker_stops import (
    BROKER_STOP_ORDER_LABEL,
    active_broker_stop_orders,
    active_broker_stop_refs,
)
from contracts.common import Explanation, Money, Provenance
from contracts.execution import ExecutionResult, Fill
from contracts.portfolio_manager import OrderIntent
from kernel import CollectingFaultSink, InMemoryGraphStore


def test_surviving_position_keeps_its_stop() -> None:
    """EXEC-IDN-03 / ADR-0015 s3: only the exited position is freed."""
    graph = InMemoryGraphStore()
    broker = EventBroker()
    sink = CollectingFaultSink()
    sold_ref = held(graph, "ABT", 191)
    kept_ref = held(graph, "BAC", 503)
    resting_stop(graph, "ABT", sold_ref)
    resting_stop(graph, "BAC", kept_ref)

    freed = cancel_stops_for_exits(
        graph, broker, sink, order_set("pm-one", sell("ABT", 191, sold_ref))
    )

    assert freed == frozenset({"ABT"})
    assert broker.events == [("cancel", f"broker:stop:{sold_ref}:ABT")]
    assert active_broker_stop_refs(graph) == frozenset({kept_ref})


def test_cancelling_an_exit_stop_is_idempotent() -> None:
    """EXEC-IDM-01: replaying the same PMRun cancels once and stays quiet."""
    graph = InMemoryGraphStore()
    broker = EventBroker()
    sink = CollectingFaultSink()
    ref = held(graph, "ABT", 191)
    resting_stop(graph, "ABT", ref)
    payload = order_set("pm-idem", sell("ABT", 191, ref))

    first = cancel_stops_for_exits(graph, broker, sink, payload)
    second = cancel_stops_for_exits(graph, broker, sink, payload)

    assert first == frozenset({"ABT"})
    assert second == frozenset()
    assert broker.events == [("cancel", f"broker:stop:{ref}:ABT")]
    assert sink.faults == []


def test_cancellation_is_an_appended_marker_not_a_deletion() -> None:
    """EXEC-OBS-03 / EXEC-IDN-03: cancellation is a cancelled_at marker on the
    immutable placement fact, and the broker remains truth for liveness."""
    graph = InMemoryGraphStore()
    broker = EventBroker()
    sink = CollectingFaultSink()
    ref = held(graph, "ABT", 191)
    key = resting_stop(graph, "ABT", ref)

    cancel_stops_for_exits(
        graph, broker, sink, order_set("pm-mark", sell("ABT", 191, ref))
    )

    stop = graph.get_node(BROKER_STOP_ORDER_LABEL, key)
    assert stop is not None, "the placement fact must survive cancellation"
    assert stop.props["cancelled_at"]
    assert stop.props["placed_at"] == "2026-07-28T08:00:44+00:00"
    assert active_broker_stop_orders(graph) == ()


def test_a_buy_cancels_no_stop() -> None:
    """EXEC-NEV-01: execution frees only what the PM approved as an exit."""
    graph = InMemoryGraphStore()
    broker = EventBroker()
    sink = CollectingFaultSink()
    ref = held(graph, "ABT", 191)
    resting_stop(graph, "ABT", ref)
    buy = OrderIntent(
        ticker="ABT",
        action="buy",
        quantity=5,
        est_price=Money(amount=Decimal("100.00")),
        rationale=Explanation(summary="fixture buy"),
    )

    freed = cancel_stops_for_exits(graph, broker, sink, order_set("pm-buy", buy))

    assert freed == frozenset()
    assert broker.events == []
    assert active_broker_stop_refs(graph) == frozenset({ref})


def test_unprotected_report_ignores_tickers_that_were_never_freed() -> None:
    """EXEC-OBS-03: only a freed position can end the run unprotected."""
    sink = CollectingFaultSink()
    result = ExecutionResult(
        run_id="run",
        stage="paper",
        fills=(
            Fill(
                ticker="BAC",
                side="sell",
                quantity=503,
                price=Money(amount=Decimal("60.00")),
                broker_order_id="rejected:BAC",
                status="rejected",
            ),
        ),
        submitted=0,
        rejected=1,
        provenance=Provenance(
            run_id="run",
            source_agent="execution",
            graph_node_id="ExecutionRun:run",
        ),
    )

    report_unprotected_exits(sink, result, frozenset({"ABT"}))

    assert sink.faults == []
