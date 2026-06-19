"""Dispatcher RPC step helpers — P14 residual.

Agent: orchestration
Role: thin RPC wrappers for narrative and supervisor steps. The per-agent pipeline
      steps (scan→report) are now event-driven via agent pub/sub; not called here.
External I/O: none; uses the injected message bus.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

from contracts.reporter import NarrativeRequest, TradeNarrative
from contracts.supervisor import DispatchResult, DispatchRunRecord
from kernel import AgentMessage, CollectingFaultSink
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from kernel import FaultSink, MessageBus


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


def step_record_dispatch_run(
    bus: MessageBus, record: DispatchRunRecord, sink: FaultSink | None = None
) -> DispatchResult | None:
    """Send supervisor one complete dispatcher run record."""
    return _request(
        bus,
        _message("supervisor", "record_dispatch_run", record),
        DispatchResult,
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
