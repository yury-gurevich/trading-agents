"""Monitor pub/sub handler.

Agent: monitor
Role: resolve execution.fills.ready claim-check events, check positions,
      and publish monitor.decisions.ready via claim-check.
External I/O: none.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from contracts.execution import ExecutionResult
from contracts.monitor import CloseDecisionSet, MonitorRequest
from kernel import GraphStore, claim_check_read, claim_check_write

if TYPE_CHECKING:
    from collections.abc import Callable

    from kernel import MessageBus


def on_fills_ready(
    bus: MessageBus,
    graph: GraphStore,
    check_positions: Callable[[MonitorRequest], CloseDecisionSet],
    event: dict[str, Any],
) -> None:
    """Handle execution.fills.ready: check positions and publish decisions."""
    run_id: str | None = event.get("run_id")
    node = claim_check_read(graph, event)
    exec_result = ExecutionResult.model_validate(node.props["result"])
    # pm_run_id threaded from execution so we find the PMRun node for positions.
    pm_run_id = str(node.props.get("pm_run_id") or exec_result.run_id)
    decisions = check_positions(MonitorRequest(run_id=pm_run_id))
    claim_check_write(
        bus,
        graph,
        topic="monitor.decisions.ready",
        label="MonitorDecisionResult",
        ref=f"monitor:{run_id or uuid.uuid4().hex}",
        props={
            "decisions": decisions.model_dump(mode="json"),
            "pm_run_id": pm_run_id,
        },
        run_id=run_id,
    )
