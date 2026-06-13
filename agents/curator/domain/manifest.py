"""Dataset manifest assembly and version numbering.

Agent: curator
Role: compute the next dataset version and build the DatasetManifest payload.
External I/O: GraphStore reads (version lookup).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.common import Explanation, Provenance
from contracts.curator import DatasetManifest, DatasetSplit, PredictorManifest

if TYPE_CHECKING:
    from agents.curator.domain.split import SplitAssignment
    from agents.curator.domain.training import TrainingResult
    from kernel import GraphStore

_MAX_EVIDENCE_REFS = 10


def next_version(graph: GraphStore, purpose: str) -> int:
    """Next 1-based version for this purpose = count of existing Dataset nodes + 1."""
    existing = [
        node
        for node in graph.list_nodes("Dataset")
        if node.props.get("purpose") == purpose
    ]
    return len(existing) + 1


def build_manifest(
    *,
    purpose: str,
    schema_ref: str,
    split: SplitAssignment,
    dataset_id: str,
    version: int,
) -> DatasetManifest:
    """Assemble the DatasetManifest from a SplitAssignment."""
    n_train, n_val, n_test = len(split.train), len(split.validation), len(split.test)
    example_count = n_train + n_val + n_test
    refs = tuple(
        record.source_ref
        for group in (split.train, split.validation, split.test)
        for record in group
    )[:_MAX_EVIDENCE_REFS]
    return DatasetManifest(
        dataset_id=dataset_id,
        version=version,
        purpose=purpose,
        example_count=example_count,
        splits=(
            DatasetSplit(name="train", example_count=n_train),
            DatasetSplit(name="validation", example_count=n_val),
            DatasetSplit(name="test", example_count=n_test),
        ),
        schema_ref=schema_ref,
        explanation=Explanation(
            summary=(
                f"{example_count} examples for {purpose} (v{version}): "
                f"{n_train}/{n_val}/{n_test} train/val/test"
            ),
            evidence_refs=refs,
        ),
        provenance=Provenance(
            run_id=dataset_id,
            source_agent="curator",
            graph_node_id=f"Dataset:{dataset_id}",
        ),
    )


def next_predictor_version(graph: GraphStore, purpose: str, target: str) -> int:
    """Next 1-based predictor version for this (purpose, target) pair."""
    existing = [
        node
        for node in graph.list_nodes("Predictor")
        if node.props.get("purpose") == purpose and node.props.get("target") == target
    ]
    return len(existing) + 1


def build_predictor_manifest(
    *,
    purpose: str,
    target: str,
    dataset_id: str,
    version: int,
    result: TrainingResult,
) -> PredictorManifest:
    """Assemble the PredictorManifest from a TrainingResult (always advisory)."""
    predictor_id = f"predictor:{purpose}:{target}:v{version}"
    accuracy = result.metrics["accuracy"]
    test_size = int(result.metrics["test_size"])
    return PredictorManifest(
        predictor_id=predictor_id,
        dataset_id=dataset_id,
        purpose=purpose,
        target=target,
        strategy=result.strategy,
        metrics=dict(result.metrics),
        sample_size=result.sample_size,
        advisory=True,
        promotion_eligible=False,
        explanation=Explanation(
            summary=(
                f"{result.strategy} predictor for {target} on {dataset_id}: "
                f"accuracy {accuracy:.2f} over {test_size} test examples "
                f"(advisory; not promoted)."
            )
        ),
        provenance=Provenance(
            run_id=predictor_id,
            source_agent="curator",
            graph_node_id=f"Predictor:{predictor_id}",
        ),
    )


def degraded_predictor_manifest(
    *, purpose: str, target: str, strategy: str, reason: str
) -> PredictorManifest:
    """Advisory manifest for a training trigger that wrote no Predictor node."""
    predictor_id = f"predictor:{purpose}:{target}:v0"
    return PredictorManifest(
        predictor_id=predictor_id,
        dataset_id="",
        purpose=purpose,
        target=target,
        strategy=strategy,
        metrics={},
        sample_size=0,
        advisory=True,
        promotion_eligible=False,
        explanation=Explanation(summary=reason),
        provenance=Provenance(
            run_id=predictor_id,
            source_agent="curator",
            graph_node_id=None,
        ),
    )
