"""Monitor-to-execution bus dispatch helpers.

Agent: monitor
Role: send close decisions to execution over the message bus.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from kernel import AgentMessage, FaultSink, MessageBus
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from contracts.monitor import CloseDecisionSet


def dispatch_closes(bus: MessageBus, sink: FaultSink, result: CloseDecisionSet) -> None:
    """Send close decisions to execution, recording any dispatch fault."""
    if not any(item.decision == "close" for item in result.decisions):
        return
    with fault_boundary(
        sink,
        agent="monitor",
        module="agents.monitor.execution_client",
        capability="check_positions",
        reraise=False,
    ):
        response = bus.request(
            AgentMessage(
                sender="monitor",
                recipient="execution",
                message_type="request",
                capability="execute_close",
                payload=result.model_dump(mode="json"),
            )
        )
        if response.message_type == "error":
            raise RuntimeError(str(response.payload.get("message", "execution error")))
