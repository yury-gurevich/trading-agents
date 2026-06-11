"""Evidence collection from the provenance graph.

Agent: researcher
Role: read Snapshot nodes from the graph and reduce them to evidence statistics.
External I/O: GraphStore reads (never writes).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel import GraphStore, Node


@dataclass(frozen=True)
class RunEvidence:
    """Reduced metrics from reporter Snapshot nodes."""

    snapshot_count: int
    avg_confidence: float
    avg_approval_rate: float
    avg_rejection_count: float


def collect_evidence(graph: GraphStore, min_sample_runs: int) -> RunEvidence | None:
    """Return evidence reduced from Snapshot nodes, or None if samples are scarce."""
    snapshots = graph.list_nodes("Snapshot")
    if len(snapshots) < min_sample_runs:
        return None
    return RunEvidence(
        snapshot_count=len(snapshots),
        avg_confidence=_average(snapshots, "signal", "avg_confidence"),
        avg_approval_rate=_average(snapshots, "portfolio", "approval_rate"),
        avg_rejection_count=_average(snapshots, "signal", "rejection_count"),
    )


def _average(nodes: tuple[Node, ...], section: str, key: str) -> float:
    return sum(_metric(node, section, key) for node in nodes) / len(nodes)


def _metric(node: Node, section: str, key: str) -> float:
    metrics = node.props.get("metrics", {})
    if not isinstance(metrics, Mapping):
        return 0.0
    values = metrics.get(section, {})
    if not isinstance(values, Mapping):
        return 0.0
    return _number(values.get(key, 0.0))


def _number(value: object) -> float:
    if not isinstance(value, int | float | str):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
