"""Curator manifest tests.

Agent: curator
Role: verify per-purpose versioning and manifest construction.
External I/O: none.
"""

from __future__ import annotations

from agents.curator.domain.manifest import build_manifest, next_version
from agents.curator.domain.split import SplitAssignment
from agents.curator.tests.test_split import _records
from kernel import InMemoryGraphStore


def test_next_version_counts_per_purpose() -> None:
    graph = InMemoryGraphStore()
    assert next_version(graph, "x") == 1

    graph.merge_node("Dataset", "dataset:x:v1", {"purpose": "x"})

    assert next_version(graph, "x") == 2
    assert next_version(graph, "y") == 1


def test_build_manifest_assembles_splits() -> None:
    split = SplitAssignment(_records(8), _records(1), _records(1))

    manifest = build_manifest(
        purpose="x",
        schema_ref="curator.training_example.v1",
        split=split,
        dataset_id="dataset:x:v1",
        version=1,
    )

    assert manifest.dataset_id == "dataset:x:v1"
    assert manifest.example_count == 10
    assert len(manifest.splits) == 3
    assert manifest.explanation.summary
