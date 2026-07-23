"""ExecutionAgent capability tests.

Agent: execution
Role: verify paper submit, close, reconcile, and stage-status behavior.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from agents.execution.broker import PaperBroker
from agents.execution.tests.helpers import (
    close_message,
    fill_node_count,
    order,
    order_set,
    reconcile_message,
    seed_order_nodes,
    stage_status_message,
    submit_message,
    wire,
)
from contracts.common import Explanation, Money, Provenance
from contracts.execution import ExecutionResult, ReconcileResult, StageStatus
from contracts.monitor import CloseDecision, CloseDecisionSet

if TYPE_CHECKING:
    import pytest


def test_submit_is_idempotent_per_order_intent() -> None:
    """EXEC-IDM-01 / EXEC-IDM-02 / EXEC-NEV-03: same OrderIntentSet replays identically;
    broker called once per intent; client_order_id never omitted."""
    bus, graph, broker, _sink = wire()
    payload = order_set(order("AAPL"), order("MSFT"))
    seed_order_nodes(graph, payload)

    first = ExecutionResult.model_validate(bus.request(submit_message(payload)).payload)
    replay = ExecutionResult.model_validate(
        bus.request(submit_message(payload)).payload
    )

    assert first == replay
    assert broker.order_count == 2
    assert fill_node_count(graph) == 2
    assert first.submitted == 2
    assert first.rejected == 0


def test_submit_records_fill_cents_and_executes_lineage() -> None:
    """EXEC-IN-01 / EXEC-TRG-01 / EXEC-OUT-01 / EXEC-OUT-02 / EXEC-TYP-01:
    EXEC-STA-03 / EXEC-OBS-01: fill Decimal cents; Fill→OrderIntent lineage."""
    bus, graph, _broker, _sink = wire()
    payload = order_set(order("AAPL", price="123.45"))
    seed_order_nodes(graph, payload)

    result = ExecutionResult.model_validate(
        bus.request(submit_message(payload)).payload
    )

    fill = graph.get_node("Fill", f"{payload.run_id}:AAPL:buy")
    assert result.fills[0].price == Money(amount=Decimal("123.45"))
    assert fill is not None
    assert fill.props["price_cents"] == 12345
    assert [node.label for node in graph.descendants(fill, max_depth=1)] == [
        "OrderIntent"
    ]


def test_broker_rejection_records_rejected_fill_and_fault() -> None:
    """EXEC-FAIL-01 / EXEC-TYP-02 / EXEC-OBS-02: broker rejection → Fill(rejected) +
    fault recorded; status ∈ allowed set; no exception to caller."""
    bus, graph, _broker, sink = wire(broker=PaperBroker(reject_tickers={"AAPL"}))
    payload = order_set(order("AAPL"))
    seed_order_nodes(graph, payload)

    result = ExecutionResult.model_validate(
        bus.request(submit_message(payload)).payload
    )
    replay = ExecutionResult.model_validate(
        bus.request(submit_message(payload)).payload
    )

    fill = graph.get_node("Fill", f"{payload.run_id}:AAPL:buy")
    assert result.submitted == 0
    assert result.rejected == 1
    assert replay.fills == result.fills
    assert result.fills[0].status == "rejected"
    assert fill is not None
    assert fill.props["reason"] == "paper_broker_rejected"
    assert len(sink.faults) == 2


def test_broker_failure_records_rejected_fill_and_fault(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """EXEC-FAIL-02 / EXEC-NEV-01: total broker failure → all rejected + fault."""
    broker = PaperBroker()
    bus, graph, _broker, sink = wire(broker=broker)
    payload = order_set(order("AAPL"))
    seed_order_nodes(graph, payload)

    def fail_submit(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("broker offline")

    monkeypatch.setattr(broker, "submit", fail_submit)

    result = ExecutionResult.model_validate(
        bus.request(submit_message(payload)).payload
    )

    fill = graph.get_node("Fill", f"{payload.run_id}:AAPL:buy")
    assert result.rejected == 1
    assert fill is not None
    assert fill.props["reason"] == "broker offline"
    assert len(sink.faults) == 1


def test_execute_close_stage_status_and_reconcile() -> None:
    """EXEC-IN-02 / EXEC-TRG-03 / EXEC-TRG-05 / EXEC-OUT-04: execute_close,
    stage_status, and reconcile return typed results."""
    bus, _graph, _broker, _sink = wire()
    close_set = CloseDecisionSet(
        run_id="monitor-run-1",
        decisions=(
            CloseDecision(
                ticker="AAPL",
                position_id="position-1",
                decision="close",
                trigger="target",
                rationale=Explanation(summary="target reached"),
                quantity=40,
                reference_price_cents=19_250,
            ),
            CloseDecision(
                ticker="MSFT",
                position_id="position-2",
                decision="hold",
                trigger="none",
                rationale=Explanation(summary="still inside policy"),
                quantity=15,
                reference_price_cents=41_000,
            ),
        ),
        positions_checked=2,
        explanation=Explanation(summary="fixture monitor pass"),
        provenance=Provenance(run_id="monitor-run-1", source_agent="monitor"),
    )

    close = ExecutionResult.model_validate(
        bus.request(close_message(close_set)).payload
    )
    reconcile = ReconcileResult.model_validate(bus.request(reconcile_message()).payload)
    status = StageStatus.model_validate(bus.request(stage_status_message()).payload)

    assert [fill.side for fill in close.fills] == ["sell"]
    assert close.submitted == 1
    # The exit sells the whole position at the decided price, not a fixture stub.
    assert [fill.quantity for fill in close.fills] == [40]
    assert [fill.price.amount for fill in close.fills] == [Decimal("192.50")]
    assert reconcile.matched == 1
    assert reconcile.discrepancies == ()
    assert status.stage == "paper"
    assert status.idempotent is True


def test_reconcile_reports_unrecorded_broker_fill() -> None:
    """EXEC-OUT-04 / EXEC-STA-01: unrecorded fill surfaces as reconcile discrepancy."""
    broker = PaperBroker()
    bus, _graph, _broker, _sink = wire(broker=broker)
    broker.submit(
        "external:AAPL:buy",
        "AAPL",
        "buy",
        1,
        Money(amount=Decimal("10.00")),
    )

    result = ReconcileResult.model_validate(bus.request(reconcile_message()).payload)

    assert result.matched == 0
    assert result.discrepancies == ("external:AAPL:buy: unrecorded_broker_fill",)
