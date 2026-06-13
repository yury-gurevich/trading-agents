"""Deterministic baseline training over a curated dataset.

Agent: curator
Role: fit a majority-class baseline on the train split and score it on the test split.
External I/O: GraphStore reads (never writes).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

    from kernel import GraphStore, Node

_TRAIN = "train"
_TEST = "test"


@dataclass(frozen=True)
class TrainingResult:
    """One deterministic training outcome with frozen evidence."""

    strategy: str
    prediction: str  # the majority label chosen on train
    metrics: Mapping[str, float]  # {"accuracy", "train_size", "test_size"}
    sample_size: int  # test-split size


def select_dataset(graph: GraphStore, purpose: str, version: int | None) -> Node | None:
    """Return the Dataset node for (purpose, version); latest when version is None."""
    matches = [
        node
        for node in graph.list_nodes("Dataset")
        if node.props.get("purpose") == purpose
    ]
    if not matches:
        return None
    if version is not None:
        return next(
            (node for node in matches if node.props.get("version") == version),
            None,
        )
    return max(matches, key=lambda node: int(node.props.get("version", 0)))


def train_baseline(
    graph: GraphStore, dataset: Node, *, strategy: str
) -> TrainingResult | None:
    """Fit majority-class on the train split, score on test; None if train empty."""
    train_labels, test_labels = _split_labels(graph, dataset)
    if not train_labels:
        return None
    prediction = _majority(train_labels)
    n_test = len(test_labels)
    hits = sum(1 for label in test_labels if label == prediction)
    accuracy = hits / n_test if n_test else 0.0
    return TrainingResult(
        strategy=strategy,
        prediction=prediction,
        metrics={
            "accuracy": float(accuracy),
            "train_size": float(len(train_labels)),
            "test_size": float(n_test),
        },
        sample_size=n_test,
    )


def _split_labels(graph: GraphStore, dataset: Node) -> tuple[list[str], list[str]]:
    prefix = f"{dataset.key}:"
    train: list[str] = []
    test: list[str] = []
    for node in graph.list_nodes("TrainingExample"):
        if not node.key.startswith(prefix):
            continue
        split = node.props.get("split")
        label = str(node.props.get("label", ""))
        if split == _TRAIN:
            train.append(label)
        elif split == _TEST:
            test.append(label)
    return train, test


def _majority(labels: list[str]) -> str:
    counts = Counter(labels)
    top = max(counts.values())
    return min(label for label, count in counts.items() if count == top)
