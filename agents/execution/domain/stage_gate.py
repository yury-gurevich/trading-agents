"""Stage gate evidence and transition checks.

Agent: execution
Role: determine whether evidence supports stage promotion; never write to graph.
External I/O: GraphStore reads.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from agents.execution.domain.stage_metrics import avg_approval_rate

if TYPE_CHECKING:
    from agents.execution.settings import ExecutionSettings
    from contracts.execution import ExecutionStage
    from kernel import GraphStore

STAGE_ORDER: tuple[ExecutionStage, ...] = (
    "paper",
    "broker_shadow",
    "live_manual",
    "live_autopilot",
)


@dataclass(frozen=True)
class StageEvidence:
    """Reduced evidence used by execution stage promotion."""

    snapshot_count: int
    avg_approval_rate: float
    critical_fault_count: int


def collect_stage_evidence(graph: GraphStore) -> StageEvidence:
    """Reduce Snapshot and Fault nodes into stage promotion evidence."""
    snapshots = graph.list_nodes("Snapshot")
    return StageEvidence(
        snapshot_count=len(snapshots),
        avg_approval_rate=avg_approval_rate(snapshots),
        critical_fault_count=sum(
            fault.props.get("severity") == "critical"
            for fault in graph.list_nodes("Fault")
        ),
    )


def check_promotion_allowed(
    evidence: StageEvidence,
    settings: ExecutionSettings,
) -> tuple[bool, str]:
    """Return whether promotion evidence is sufficient and why."""
    if evidence.snapshot_count < settings.min_promotion_runs:
        reason = (
            f"need {settings.min_promotion_runs} runs; have {evidence.snapshot_count}"
        )
        return False, reason
    if evidence.avg_approval_rate < settings.min_approval_rate:
        reason = (
            f"approval_rate {evidence.avg_approval_rate:.2f} "
            f"below {settings.min_approval_rate:.2f}"
        )
        return False, reason
    if evidence.critical_fault_count > 0:
        return False, f"{evidence.critical_fault_count} critical fault(s) unresolved"
    return True, "evidence gate passed"


def is_valid_promotion(from_stage: ExecutionStage, to_stage: ExecutionStage) -> bool:
    """Return True when target is the next supported promotion stage."""
    if to_stage == "live_autopilot":
        return False
    return STAGE_ORDER.index(to_stage) == STAGE_ORDER.index(from_stage) + 1


def is_valid_demotion(from_stage: ExecutionStage, to_stage: ExecutionStage) -> bool:
    """Return True when target is any earlier stage."""
    return STAGE_ORDER.index(to_stage) < STAGE_ORDER.index(from_stage)
