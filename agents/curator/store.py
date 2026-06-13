"""Curator graph write path.

Agent: curator
Role: write Dataset and TrainingExample nodes and link them to source provenance.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.curator.domain.assembly import ExampleRecord
    from agents.curator.domain.split import SplitAssignment
    from contracts.curator import DatasetManifest, PredictorManifest
    from kernel import GraphStore, Node

_NARRATIVE_PREFIX = "TradeNarrative:"


def write_dataset(
    graph: GraphStore, *, manifest: DatasetManifest, split: SplitAssignment
) -> None:
    """Write the Dataset node, one TrainingExample per record, and provenance edges."""
    dataset = graph.merge_node(
        "Dataset",
        manifest.dataset_id,
        {
            "purpose": manifest.purpose,
            "version": manifest.version,
            "example_count": manifest.example_count,
            "schema_ref": manifest.schema_ref,
            "train_count": len(split.train),
            "validation_count": len(split.validation),
            "test_count": len(split.test),
            "created_at": datetime.now(tz=UTC).isoformat(),
        },
    )
    for name, records in (
        ("train", split.train),
        ("validation", split.validation),
        ("test", split.test),
    ):
        for record in records:
            _write_example(graph, dataset, manifest, name, record)


def _write_example(
    graph: GraphStore,
    dataset: Node,
    manifest: DatasetManifest,
    split_name: str,
    record: ExampleRecord,
) -> None:
    example = graph.merge_node(
        "TrainingExample",
        f"{manifest.dataset_id}:{record.example_id}",
        {
            "purpose": manifest.purpose,
            "split": split_name,
            "content": record.content,
            "label": record.label,
            "source_ref": record.source_ref,
            **record.metadata,
        },
    )
    graph.add_edge(dataset, example, "CONTAINS")
    source = _source_node(graph, record.source_ref)
    if source is not None:
        graph.add_edge(example, source, "DERIVED_FROM")


def _source_node(graph: GraphStore, source_ref: str) -> Node | None:
    if not source_ref.startswith(_NARRATIVE_PREFIX):
        return None
    return graph.get_node("TradeNarrative", source_ref[len(_NARRATIVE_PREFIX) :])


def write_predictor(
    graph: GraphStore, *, manifest: PredictorManifest, dataset: Node
) -> None:
    """Write the Predictor node (frozen evidence) and link it to its Dataset."""
    predictor = graph.merge_node(
        "Predictor",
        manifest.predictor_id,
        {
            "purpose": manifest.purpose,
            "target": manifest.target,
            "strategy": manifest.strategy,
            "accuracy": manifest.metrics["accuracy"],
            "train_size": manifest.metrics["train_size"],
            "test_size": manifest.metrics["test_size"],
            "sample_size": manifest.sample_size,
            "advisory": manifest.advisory,
            "promotion_eligible": manifest.promotion_eligible,
            "dataset_id": manifest.dataset_id,
            "trained_at": datetime.now(tz=UTC).isoformat(),
        },
    )
    graph.add_edge(predictor, dataset, "TRAINED_ON")


def write_promotion(graph: GraphStore, *, predictor: Node, approval_ref: str) -> Node:
    """Append the PredictorPromotion audit node and link it to its Predictor."""
    promotion = graph.merge_node(
        "PredictorPromotion",
        f"promotion:{predictor.key}",
        {
            "predictor_id": predictor.key,
            "from_state": "advisory",
            "to_state": "load_bearing",
            "accuracy": predictor.props.get("accuracy"),
            "sample_size": predictor.props.get("sample_size"),
            "approval_ref": approval_ref,
            "promoted_at": datetime.now(tz=UTC).isoformat(),
        },
    )
    graph.add_edge(promotion, predictor, "PROMOTES")
    return promotion
