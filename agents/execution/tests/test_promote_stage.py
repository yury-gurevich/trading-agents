"""Execution stage-promotion capability tests.

Agent: execution
Role: verify promotion confirmation, demotion, stage status, and live submission gate.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.execution.store import write_stage_transition
from agents.execution.tests.helpers import (
    order,
    order_set,
    seed_order_nodes,
    stage_status_message,
    submit_message,
    wire,
)
from agents.execution.tests.stage_helpers import (
    promote_message,
    resolve_stage_flag,
    seed_stage_snapshots,
)
from contracts.execution import ExecutionResult, PromoteStageResult, StageStatus

if TYPE_CHECKING:
    from kernel import InProcessBus


def test_promote_stage_blocked_without_evidence() -> None:
    bus, graph, _broker, _sink = wire()

    result = _promote(bus, "broker_shadow")

    assert result.accepted is False
    assert "need" in result.reason
    assert graph.list_nodes("Flag") == ()


def test_promote_stage_writes_flag_when_evidence_passes() -> None:
    bus, graph, _broker, _sink = wire()
    seed_stage_snapshots(graph, approval_rate=0.80)

    result = _promote(bus, "broker_shadow")

    assert result.accepted is False
    assert "confirmation required" in result.reason
    assert graph.list_nodes("Flag")
    assert graph.list_nodes("StageTransition") == ()


def test_confirmed_without_resolution_still_requires_confirmation() -> None:
    bus, graph, _broker, _sink = wire()
    seed_stage_snapshots(graph, approval_rate=0.80)

    result = _promote(bus, "broker_shadow", confirmed=True)

    assert result.accepted is False
    assert "confirmation required" in result.reason
    assert graph.list_nodes("Flag")


def test_promote_stage_confirmed_writes_transition_and_status_reads_graph() -> None:
    bus, graph, _broker, _sink = wire()
    seed_stage_snapshots(graph, approval_rate=0.80)
    resolve_stage_flag(graph, "broker_shadow")

    result = _promote(bus, "broker_shadow", confirmed=True)
    status = StageStatus.model_validate(bus.request(stage_status_message()).payload)

    assert result.accepted is True
    assert result.current_stage == "broker_shadow"
    assert status.stage == "broker_shadow"
    assert len(graph.list_nodes("StageTransition")) == 1


def test_demotion_is_immediate_and_invalid_promotion_is_rejected() -> None:
    bus, graph, _broker, _sink = wire()
    write_stage_transition(
        graph, from_stage="paper", to_stage="broker_shadow", reason="fixture"
    )

    demotion = _promote(bus, "paper")
    invalid = _promote(bus, "live_manual")

    assert demotion.accepted is True
    assert demotion.current_stage == "paper"
    assert invalid.accepted is False
    assert "invalid transition" in invalid.reason


def test_submit_rejects_live_manual_without_broker_call() -> None:
    bus, graph, broker, _sink = wire()
    write_stage_transition(
        graph, from_stage="paper", to_stage="live_manual", reason="x"
    )
    payload = order_set(order("AAPL"))
    seed_order_nodes(graph, payload)

    result = ExecutionResult.model_validate(
        bus.request(submit_message(payload)).payload
    )

    assert result.stage == "live_manual"
    assert result.submitted == 0
    assert result.rejected == 1
    assert broker.order_count == 0
    assert graph.list_nodes("Fill")[0].props["status"] == "rejected"


def _promote(
    bus: InProcessBus, target_stage: str, *, confirmed: bool = False
) -> PromoteStageResult:
    response = bus.request(promote_message(target_stage, confirmed=confirmed))
    return PromoteStageResult.model_validate(response.payload)
