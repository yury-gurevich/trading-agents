"""Dataset manifest assembly and version numbering.

Agent: curator
Role: compute the next dataset version and build the DatasetManifest payload.
External I/O: GraphStore reads (version lookup).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.common import Explanation, Provenance
from contracts.curator import DatasetManifest, DatasetSplit

if TYPE_CHECKING:
    from agents.curator.domain.split import SplitAssignment
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
