"""Deterministic baseline trainer tests.

Agent: curator
Role: verify majority-class fit, accuracy scoring, tie-break, and dataset selection.
External I/O: none.
"""

from __future__ import annotations

from agents.curator.domain.training import (
    select_dataset,
    train_baseline,
)
from kernel import InMemoryGraphStore, Node

_STRATEGY = "majority_class"


def _dataset(graph: InMemoryGraphStore, version: int) -> Node:
    return graph.merge_node(
        "Dataset",
        f"dataset:exit-timing:v{version}",
        {"purpose": "exit-timing", "version": version},
    )


def _example(
    graph: InMemoryGraphStore, dataset: Node, eid: str, split: str, label: str
) -> None:
    graph.merge_node(
        "TrainingExample",
        f"{dataset.key}:{eid}",
        {"purpose": "exit-timing", "split": split, "label": label},
    )


def test_majority_class_scores_test_split() -> None:
    graph = InMemoryGraphStore()
    dataset = _dataset(graph, 1)
    for i, label in enumerate(("target", "target", "stop")):
        _example(graph, dataset, f"tr{i}", "train", label)
    _example(graph, dataset, "te0", "test", "target")

    result = train_baseline(graph, dataset, strategy=_STRATEGY)

    assert result is not None
    assert result.prediction == "target"
    assert result.metrics["accuracy"] == 1.0
    assert result.metrics["train_size"] == 3.0
    assert result.metrics["test_size"] == 1.0


def test_tie_breaks_alphabetically() -> None:
    graph = InMemoryGraphStore()
    dataset = _dataset(graph, 1)
    _example(graph, dataset, "tr0", "train", "stop")
    _example(graph, dataset, "tr1", "train", "target")

    result = train_baseline(graph, dataset, strategy=_STRATEGY)

    assert result is not None
    assert result.prediction == "stop"


def test_empty_test_split_is_valid() -> None:
    graph = InMemoryGraphStore()
    dataset = _dataset(graph, 1)
    _example(graph, dataset, "tr0", "train", "target")

    result = train_baseline(graph, dataset, strategy=_STRATEGY)

    assert result is not None
    assert result.metrics["accuracy"] == 0.0
    assert result.metrics["test_size"] == 0.0
    assert result.sample_size == 0


def test_empty_train_split_returns_none() -> None:
    graph = InMemoryGraphStore()
    dataset = _dataset(graph, 1)
    _example(graph, dataset, "te0", "test", "target")

    assert train_baseline(graph, dataset, strategy=_STRATEGY) is None


def test_ignores_other_datasets_and_validation_split() -> None:
    graph = InMemoryGraphStore()
    dataset = _dataset(graph, 1)
    other = _dataset(graph, 2)
    _example(graph, dataset, "tr0", "train", "stop")
    _example(graph, dataset, "va0", "validation", "target")
    _example(graph, other, "tr0", "train", "target")

    result = train_baseline(graph, dataset, strategy=_STRATEGY)

    assert result is not None
    assert result.prediction == "stop"
    assert result.metrics["train_size"] == 1.0


def test_select_dataset_latest_exact_and_missing() -> None:
    graph = InMemoryGraphStore()
    _dataset(graph, 1)
    _dataset(graph, 2)

    latest = select_dataset(graph, "exit-timing", None)
    exact = select_dataset(graph, "exit-timing", 1)

    assert latest is not None
    assert latest.props["version"] == 2
    assert exact is not None
    assert exact.props["version"] == 1
    assert select_dataset(graph, "unknown", None) is None
    assert select_dataset(graph, "exit-timing", 9) is None
