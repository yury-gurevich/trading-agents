"""Execution result builders.

Agent: execution
Role: convert broker fills into public execution payloads.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.execution.domain.orders import fill_from_broker
from contracts.execution import ExecutionResult, Fill

if TYPE_CHECKING:
    from agents.execution.broker import BrokerFill
    from contracts.common import Provenance
    from contracts.execution import ExecutionStage


def execution_result(
    run_id: str,
    stage: ExecutionStage,
    fills: tuple[BrokerFill, ...],
    provenance: Provenance,
) -> ExecutionResult:
    """Build the public ExecutionResult from broker-side fills."""
    public_fills: tuple[Fill, ...] = tuple(fill_from_broker(fill) for fill in fills)
    return ExecutionResult(
        run_id=run_id,
        stage=stage,
        fills=public_fills,
        submitted=sum(fill.status != "rejected" for fill in fills),
        rejected=sum(fill.status == "rejected" for fill in fills),
        provenance=provenance,
    )
