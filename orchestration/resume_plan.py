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


LINKED_FROM_EDGE = "LINKED_FROM"
"""Every resume clone points back at the artifact it was cloned from."""

DERIVED_FROM_EDGE = "DERIVED_FROM"

REGIME_CONTEXT_LABEL = "RegimeContext"

SIDE_BRANCH_EDGES: dict[str, str] = {
    "AnalystRun": "FORECAST_BY",
    "PMRun": "DELIBERATED_BY",
}
"""Chain keys whose clone re-links a side branch, and the edge that carries it."""


def resume_edge_signatures(
    artifacts: tuple[ResumeArtifact, ...] = ARTIFACTS,
) -> frozenset[tuple[str, str, str]]:
    """Return every edge shape the resume clone path is able to write.

    Derived from the same table `resume.py` walks, because the alternative is a
    hand-kept list that drifts. The static signature scan cannot reach these
    call sites at all — they merge under ``artifact.label``, so the label never
    resolves — which is how two LINKED_FROM shapes stayed undeclared until a
    late-stage resume would have hit them under the write guard.
    """
    labels = {artifact.chain_key: artifact.label for artifact in artifacts}
    found = {(REGIME_CONTEXT_LABEL, LINKED_FROM_EDGE, REGIME_CONTEXT_LABEL)}
    for artifact in artifacts:
        parent = (
            "RunRequest" if artifact.parent == "RunRequest" else labels[artifact.parent]
        )
        found.add((parent, artifact.edge, artifact.label))
        found.add((artifact.label, LINKED_FROM_EDGE, artifact.label))
        if artifact.chain_key == "ScanRun":
            found.add((artifact.label, DERIVED_FROM_EDGE, labels["MarketData"]))
    return frozenset(found)


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
