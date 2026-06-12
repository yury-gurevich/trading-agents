"""Dataset query projections.

Agent: surfaces
Role: read Dataset nodes and project dataset views, newest first.
External I/O: GraphStore reads.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from surfaces.queries._graph import nodes_by_label

if TYPE_CHECKING:
    from kernel import GraphStore, Node


@dataclass(frozen=True)
class DatasetView:
    """Operator-facing view of one curated dataset."""

    dataset_id: str
    purpose: str
    version: int
    example_count: int
    train_count: int
    validation_count: int
    test_count: int


def all_datasets(graph: GraphStore) -> tuple[DatasetView, ...]:
    """Return all datasets, newest first (by purpose then version desc)."""
    views = (_view(node) for node in nodes_by_label(graph, "Dataset"))
    return tuple(
        sorted(views, key=lambda item: (item.purpose, item.version), reverse=True)
    )


def _view(node: Node) -> DatasetView:
    return DatasetView(
        dataset_id=str(node.props.get("dataset_id", node.key)),
        purpose=str(node.props.get("purpose", "")),
        version=int(node.props.get("version", 0)),
        example_count=int(node.props.get("example_count", 0)),
        train_count=int(node.props.get("train_count", 0)),
        validation_count=int(node.props.get("validation_count", 0)),
        test_count=int(node.props.get("test_count", 0)),
    )
