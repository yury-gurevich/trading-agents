"""Execution broker-stop defensive branch tests.

Agent: execution
Role: prove unprotected-position checks can fail loudly.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.broker_stop_thresholds import broker_stop_thresholds
from agents.execution.broker_stops import place_broker_stops
from agents.execution.tests.broker_stop_helpers import PendingStopBroker, order_set
from contracts.positions import open_positions
from kernel import CollectingFaultSink, InMemoryGraphStore, Node


def test_threshold_planner_reports_reachable_bad_lots() -> None:
    """EXEC-FAIL-01 / EXEC-OBS-02: invalid stop inputs become per-ticker errors."""
    graph = InMemoryGraphStore()
    _position(graph, "blank", "", 1)
    _position(graph, "zero", "ZERO", 0)
    _position(graph, "bool-qty", "BOOLQ", True)
    _position(graph, "bool-stop", "BOOLS", 1, stop_pct=True)
    _position(graph, "mix-a", "MIX", 1, stop_pct=0.04)
    _position(graph, "mix-b", "MIX", 1, stop_pct=0.05)

    result = broker_stop_thresholds(graph, fallback_stop_pct=0.05)

    assert result.plans == ()
    reasons = {error.ticker: error.reason for error in result.errors}
    assert "non-positive quantity" in reasons["ZERO"]
    assert "lacks stop threshold inputs" in reasons["BOOLQ"]
    assert "lacks stop threshold inputs" in reasons["BOOLS"]
    assert "different stop_pct values" in reasons["MIX"]


def test_bad_threshold_and_missing_position_emit_distinct_faults() -> None:
    """EXEC-FAIL-01 / EXEC-OBS-02: unprotected broker holdings are not silent."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    broker = PendingStopBroker()
    _position(graph, "bool-qty", "BOOLQ", True)

    place_broker_stops(
        graph,
        broker,
        sink,
        order_set("pm-run"),
        _snapshot(
            graph,
            (
                {"ticker": "BOOLQ", "quantity": 1},
                {"ticker": "MISSING", "quantity": 2},
            ),
        ),
        fallback_stop_pct=0.05,
    )

    assert broker.submitted == []
    messages = [fault.message for fault in sink.faults]
    assert any(
        "BOOLQ" in message and "no stop threshold" in message for message in messages
    )
    assert any(
        "MISSING" in message and "no active graph position" in message
        for message in messages
    )


def test_broker_quantity_mismatch_is_visible_and_blocks_submission() -> None:
    """EXEC-NEV-03 / EXEC-OBS-02: mismatched graph and broker quantities halt stops."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    broker = PendingStopBroker()
    _position(graph, "held:AAPL", "AAPL", 4)

    place_broker_stops(
        graph,
        broker,
        sink,
        order_set("pm-run"),
        _snapshot(graph, ({"ticker": "AAPL", "quantity": 3},)),
        fallback_stop_pct=0.05,
    )

    assert broker.submitted == []
    assert sink.faults[-1].context["reason"] == (
        "graph quantity 4 does not match broker quantity"
    )


def test_active_stop_fact_skips_duplicate_submission() -> None:
    """EXEC-IDM-01 / EXEC-IDM-02: an active stop fact prevents duplicate stops."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    broker = PendingStopBroker()
    _position(graph, "held:AAPL", "AAPL", 4)
    ref = open_positions(graph)[0].position_ref
    _stop_fact(graph, ref)

    place_broker_stops(
        graph,
        broker,
        sink,
        order_set("pm-run"),
        _snapshot(graph, ({"ticker": "AAPL", "quantity": 4},)),
        fallback_stop_pct=0.05,
    )

    assert broker.submitted == []
    assert sink.faults == []


def test_cancelled_stop_fact_blocks_retry_loudly() -> None:
    """EXEC-FAIL-01 / EXEC-OBS-02: inactive stop facts do not hide exposure."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    broker = PendingStopBroker()
    _position(graph, "held:AAPL", "AAPL", 4)
    ref = open_positions(graph)[0].position_ref
    _stop_fact(graph, ref, cancelled_at="2026-07-28T00:00:00Z")

    place_broker_stops(
        graph,
        broker,
        sink,
        order_set("pm-run"),
        _snapshot(graph, ({"ticker": "AAPL", "quantity": 4},)),
        fallback_stop_pct=0.05,
    )

    assert broker.submitted == []
    assert sink.faults[-1].context["reason"] == (
        "existing inactive BrokerStopOrder fact blocks retry"
    )


def _position(
    graph: InMemoryGraphStore,
    key: str,
    ticker: str,
    quantity: object,
    *,
    stop_pct: object = 0.05,
) -> None:
    graph.merge_node(
        "Position",
        key,
        {
            "run_id": "seed",
            "ticker": ticker,
            "quantity": quantity,
            "target_pct": 0.10,
            "horizon_days": 10,
            "opened_at": "2026-07-20",
            "opened_price_cents": 10000,
            "status": "open",
            "stop_pct": stop_pct,
        },
    )


def _snapshot(graph: InMemoryGraphStore, holdings: tuple[object, ...]) -> Node:
    return graph.merge_node(
        "BrokerPositionSnapshot",
        "snapshot",
        {"status": "fresh", "holdings": holdings},
    )


def _stop_fact(
    graph: InMemoryGraphStore, position_ref: str, *, cancelled_at: str | None = None
) -> None:
    props: dict[str, object] = {
        "ticker": "AAPL",
        "position_ref": position_ref,
        "stop_price_cents": 9500,
        "broker_order_id": "broker-stop-1",
        "placed_at": "2026-07-28T00:00:00Z",
    }
    if cancelled_at is not None:
        props["cancelled_at"] = cancelled_at
    graph.merge_node("BrokerStopOrder", f"stop:{position_ref}:AAPL", props)
