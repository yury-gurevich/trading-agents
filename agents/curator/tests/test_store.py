"""Curator graph write-path tests.

Agent: curator
Role: verify dataset writes skip DERIVED_FROM when the source node is absent.
External I/O: none.
"""

from __future__ import annotations

from agents.curator.domain.assembly import ExampleRecord
from agents.curator.domain.manifest import build_manifest
from agents.curator.domain.split import SplitAssignment
from agents.curator.store import write_dataset
from kernel import InMemoryGraphStore


def _record(source_ref: str) -> ExampleRecord:
    return ExampleRecord(
        example_id="exit-timing:p1",
        content="story",
        label="target",
        source_ref=source_ref,
        metadata={"run_id": "run-1", "position_id": "p1"},
    )


def _write(graph: InMemoryGraphStore, source_ref: str) -> None:
    split = SplitAssignment((_record(source_ref),), (), ())
    manifest = build_manifest(
        purpose="exit-timing",
        schema_ref="curator.training_example.v1",
        split=split,
        dataset_id="dataset:exit-timing:v1",
        version=1,
    )
    write_dataset(graph, manifest=manifest, split=split)


def test_missing_source_narrative_skips_derived_from_edge() -> None:
    graph = InMemoryGraphStore()

    _write(graph, "TradeNarrative:narrative:absent")

    example = graph.list_nodes("TrainingExample")[0]
    assert (
        tuple(graph.descendants(example, max_depth=1, edge_types={"DERIVED_FROM"}))
        == ()
    )


def test_non_narrative_source_ref_adds_no_edge() -> None:
    graph = InMemoryGraphStore()

    _write(graph, "Other:thing")

    example = graph.list_nodes("TrainingExample")[0]
    assert (
        tuple(graph.descendants(example, max_depth=1, edge_types={"DERIVED_FROM"}))
        == ()
    )
