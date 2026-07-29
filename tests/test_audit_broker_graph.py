"""Read-only broker graph audit tests.

Agent: tooling
Role: prove broker/graph audit failures are planted and predicates are shared.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from scripts.audit_broker_graph import AuditReport, AuditRow, audit_graph
from scripts.repair_orphan_fills import repair_graph

from agents.execution.broker import BrokerFill, BrokerPosition
from agents.execution.broker_stops import place_broker_stops
from agents.execution.paper_broker import PaperBroker
from agents.execution.tests.broker_stop_helpers import order_set
from contracts.common import Money
from kernel import CollectingFaultSink, InMemoryGraphStore, Node

_SINCE = datetime(2026, 7, 20, tzinfo=UTC)


def test_audit_a1_fails_duplicate_active_and_honors_supersession() -> None:
    """MON-STA-02: supersession is append-only and the active predicate owns A1."""
    graph = InMemoryGraphStore()
    _position(graph, "a:AAPL", "AAPL", 3)
    _position(graph, "b:AAPL", "AAPL", 1)
    broker_positions = (_broker_position("AAPL", 3),)

    before = audit_graph(graph, broker_positions, ())
    graph.merge_node("Position", "b:AAPL", {"broker_superseded_by": "a:AAPL"})
    after = audit_graph(graph, broker_positions, ())

    assert _row(before, "A1", "AAPL").verdict == "FAIL"
    assert _row(after, "A1", "AAPL").verdict == "OK"


def test_audit_a2_fails_missing_stop_then_passes_after_placement() -> None:
    """EXEC-DEP-03 / EXEC-OBS-02: planted no-stop condition can fail and pass."""
    graph = InMemoryGraphStore()
    broker = PaperBroker()
    sink = CollectingFaultSink()
    _position(graph, "held:AAPL", "AAPL", 2)
    broker_positions = (_broker_position("AAPL", 2),)

    before = audit_graph(graph, broker_positions, ())
    place_broker_stops(
        graph,
        broker,
        sink,
        order_set("pm-run"),
        _snapshot(graph, ({"ticker": "AAPL", "quantity": 2},)),
        fallback_stop_pct=0.05,
    )
    after = audit_graph(graph, broker_positions, broker.fills())

    assert _row(before, "A2", "AAPL").verdict == "FAIL"
    assert _row(after, "A2", "AAPL").verdict == "OK"
    assert sink.faults == []


def test_audit_a3_fails_orphan_order_then_passes_after_repair() -> None:
    """EXEC-NEV-03 / EXEC-OBS-01: orphan Fill repair closes the A3 failure."""
    graph = InMemoryGraphStore()
    _pm_lineage(graph, "pm-run-a", "HPE")
    broker_order = BrokerFill(
        "pm-run-a:HPE:buy",
        "HPE",
        "buy",
        229,
        Money(amount=Decimal("41.37")),
        "broker-hpe",
        "filled",
        submitted_at="2026-07-27T13:31:00Z",
    )

    before = audit_graph(graph, (), (broker_order,))
    repair_graph(
        graph,
        (broker_order,),
        apply=True,
        since=_SINCE,
    )
    after = audit_graph(graph, (), (broker_order,))

    assert _row(before, "A3", broker_order.idempotency_key).verdict == "FAIL"
    assert not [
        row for row in after.rows if row.check == "A3" and row.verdict == "FAIL"
    ]


def test_audit_a5_fails_unprotected_position_with_dropped_sell() -> None:
    """EXEC-OBS-02 / RPT-NEV-03: unprotected held plus dropped exit is distinct."""
    graph = InMemoryGraphStore()
    _position(graph, "held:AMD", "AMD", 3)
    graph.merge_node(
        "Fill",
        "exit:ref:AMD:sell",
        {
            "ticker": "AMD",
            "side": "sell",
            "status": "pending",
            "broker_status": "canceled",
            "drop_reason": "unfilled at session end",
        },
    )
    broker_position = _broker_position("AMD", 3)
    stop = BrokerFill(
        "custom-stop-client",
        "AMD",
        "sell",
        3,
        Money(amount=Decimal("95.00")),
        "broker-stop",
        "pending",
        order_type="stop",
    )

    before = audit_graph(graph, (broker_position,), ())
    after = audit_graph(graph, (broker_position,), (stop,))

    assert _row(before, "A5", "AMD").verdict == "FAIL"
    assert [row for row in after.rows if row.check == "A5"] == []


def _row(report: AuditReport, check: str, subject: str) -> AuditRow:
    return next(
        row for row in report.rows if row.check == check and row.subject == subject
    )


def _position(
    graph: InMemoryGraphStore,
    key: str,
    ticker: str,
    quantity: int,
) -> None:
    graph.merge_node(
        "Position",
        key,
        {
            "ticker": ticker,
            "quantity": quantity,
            "opened_price_cents": 10000,
            "stop_pct": 0.05,
            "status": "open",
        },
    )


def _pm_lineage(graph: InMemoryGraphStore, pm_run_id: str, ticker: str) -> None:
    graph.merge_node("PMRun", pm_run_id, {"status": "complete"})
    graph.merge_node("OrderIntent", f"{pm_run_id}:{ticker}", {"ticker": ticker})


def _broker_position(ticker: str, quantity: int) -> BrokerPosition:
    return BrokerPosition(
        ticker=ticker,
        quantity=quantity,
        avg_entry_cents=10000,
        market_value_cents=quantity * 10000,
    )


def _snapshot(graph: InMemoryGraphStore, holdings: tuple[object, ...]) -> Node:
    return graph.merge_node(
        "BrokerPositionSnapshot",
        "snapshot",
        {"status": "fresh", "holdings": holdings},
    )
