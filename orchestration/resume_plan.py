"""Resume artifact ordering for graph-pull runs.

Agent: orchestration
Role: keep resume stages and cloned artifacts aligned by explicit stage names.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from contracts.position_sync import POSITION_SYNC_EDGE
from contracts.resume import RESUME_STAGES, ResumeStage

if TYPE_CHECKING:
    from kernel import Node

ParentKey = Literal[
    "RunRequest",
    "MarketData",
    "ScanRun",
    "AnalystRun",
    "PMRun",
    "ExecutionRun",
    "MonitorRun",
]


@dataclass(frozen=True)
class ResumeArtifact:
    """One stage output that can be linked into a child run."""

    stage: ResumeStage
    chain_key: str
    label: str
    edge: str
    parent: ParentKey


ARTIFACTS: tuple[ResumeArtifact, ...] = (
    ResumeArtifact(
        "position_sync", "PositionSync", "MonitorRun", POSITION_SYNC_EDGE, "RunRequest"
    ),
    ResumeArtifact("provider", "MarketData", "MarketData", "INGESTED_BY", "RunRequest"),
    ResumeArtifact("scanner", "ScanRun", "ScanRun", "SCANNED_BY", "MarketData"),
    ResumeArtifact("analyst", "AnalystRun", "AnalystRun", "ANALYZED_BY", "ScanRun"),
    ResumeArtifact("pm", "PMRun", "PMRun", "EVALUATED_BY", "AnalystRun"),
    ResumeArtifact("execution", "ExecutionRun", "ExecutionRun", "EXECUTED_BY", "PMRun"),
    ResumeArtifact(
        "monitor", "MonitorRun", "MonitorRun", "MONITORED_BY", "ExecutionRun"
    ),
    ResumeArtifact("reporter", "Snapshot", "Snapshot", "REPORTED_BY", "MonitorRun"),
)


def required_artifacts(stage: ResumeStage) -> tuple[ResumeArtifact, ...]:
    """Return artifacts that must exist before resuming from ``stage``."""
    return ARTIFACTS[: RESUME_STAGES.index(stage)]


def artifact_parent(
    artifact: ResumeArtifact, child: Node, clones: dict[str, Node]
) -> Node:
    """Return the clone/root parent for one artifact edge."""
    if artifact.parent == "RunRequest":
        return child
    return clones[artifact.parent]


def validate_alignment(
    stages: tuple[ResumeStage, ...] = RESUME_STAGES,
    artifacts: tuple[ResumeArtifact, ...] = ARTIFACTS,
) -> None:
    """Fail if the stage tuple and artifact tuple drift out of order."""
    artifact_stages = tuple(artifact.stage for artifact in artifacts)
    if artifact_stages != stages:
        raise ValueError("resume artifacts are not aligned to RESUME_STAGES")
