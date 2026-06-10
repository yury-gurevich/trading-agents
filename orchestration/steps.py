"""Dispatcher pipeline steps.

Agent: orchestration
Role: send one typed bus request per pipeline stage and return typed outputs.
External I/O: none; uses the injected message bus.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

from contracts.analyst import RecommendationSet
from contracts.common import ScanRequest
from contracts.execution import ExecutionResult
from contracts.monitor import CloseDecisionSet, MonitorRequest
from contracts.portfolio_manager import OrderIntentSet
from contracts.reporter import (
    NarrativeRequest,
    RunSnapshot,
    TradeNarrative,
)
from contracts.scanner import CandidateSet
from kernel import AgentMessage, CollectingFaultSink
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from kernel import FaultSink, MessageBus
    from orchestration.trigger import RunTrigger


def step_scan(
    bus: MessageBus, trigger: RunTrigger, sink: FaultSink | None = None
) -> CandidateSet | None:
    """Run scanner and return candidates, or None when no candidates survive."""
    result = _request(
        bus,
        _message(
            "scanner",
            "run_scan",
            ScanRequest(run_id=trigger.run_id, universe=trigger.universe),
        ),
        CandidateSet,
        sink,
    )
    return result if result is not None and result.candidates else None


def step_analyze(
    bus: MessageBus, candidates: CandidateSet, sink: FaultSink | None = None
) -> RecommendationSet | None:
    """Run analyst and return actionable recommendations, or None."""
    if not candidates.candidates:
        return None
    result = _request(
        bus,
        _message("analyst", "analyze", candidates),
        RecommendationSet,
        sink,
    )
    return result if result is not None and result.recommendations else None


def step_evaluate(
    bus: MessageBus, recommendations: RecommendationSet, sink: FaultSink | None = None
) -> OrderIntentSet | None:
    """Run portfolio manager and return approved orders, or None."""
    result = _request(
        bus,
        _message("portfolio_manager", "evaluate_orders", recommendations),
        OrderIntentSet,
        sink,
    )
    return result if result is not None and result.approved else None


def step_submit(
    bus: MessageBus, orders: OrderIntentSet, sink: FaultSink | None = None
) -> ExecutionResult | None:
    """Submit approved orders and return fills, or None."""
    result = _request(
        bus, _message("execution", "submit", orders), ExecutionResult, sink
    )
    return result if result is not None and result.submitted > 0 else None


def step_check_positions(
    bus: MessageBus, pm_run_id: str, sink: FaultSink | None = None
) -> CloseDecisionSet | None:
    """Run monitor over opened positions and return decisions, or None."""
    result = _request(
        bus,
        _message("monitor", "check_positions", MonitorRequest(run_id=pm_run_id)),
        CloseDecisionSet,
        sink,
    )
    return result if result is not None and result.decisions else None


def step_report(
    bus: MessageBus, pm_run_id: str, sink: FaultSink | None = None
) -> RunSnapshot | None:
    """Run reporter snapshot generation."""
    return _request(
        bus,
        AgentMessage(
            sender="dispatcher",
            recipient="reporter",
            message_type="request",
            capability="report",
            payload={"run_id": pm_run_id},
        ),
        RunSnapshot,
        sink,
    )


def step_narrative(
    bus: MessageBus, position_id: str, sink: FaultSink | None = None
) -> TradeNarrative | None:
    """Run reporter narrative generation for one position."""
    return _request(
        bus,
        _message("reporter", "narrative", NarrativeRequest(position_id=position_id)),
        TradeNarrative,
        sink,
    )


def _request[T: BaseModel](
    bus: MessageBus,
    message: AgentMessage,
    response_type: type[T],
    sink: FaultSink | None,
) -> T | None:
    out: T | None = None
    fault_sink = sink if sink is not None else CollectingFaultSink()
    with fault_boundary(
        fault_sink,
        agent="orchestration",
        module="orchestration.steps",
        capability=message.capability,
        reraise=False,
    ) as capture:
        response = bus.request(message)
        if response.message_type == "error":
            raise RuntimeError(str(response.payload.get("message", "step failed")))
        out = response_type.model_validate(response.payload)
    return None if capture.fault is not None else out


def _message(recipient: str, capability: str, payload: BaseModel) -> AgentMessage:
    return AgentMessage(
        sender="dispatcher",
        recipient=recipient,
        message_type="request",
        capability=capability,
        payload=payload.model_dump(mode="json"),
    )
