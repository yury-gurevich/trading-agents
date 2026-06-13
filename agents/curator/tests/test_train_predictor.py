"""Curator train_predictor bus tests.

Agent: curator
Role: verify train_predictor writes an advisory Predictor, versions, and degrades.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from agents.curator import CuratorAgent
from agents.curator.tests.helpers import (
    build_dataset_message,
    seed_narratives,
    train_predictor_message,
)
from contracts.curator import DatasetManifest, PredictorManifest
from kernel import CollectingFaultSink, InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from kernel import GraphStore


def _bind(graph: InMemoryGraphStore) -> InProcessBus:
    bus = InProcessBus()
    CuratorAgent(bus, graph=graph).bind()
    return bus


def _build(bus: InProcessBus) -> DatasetManifest:
    return DatasetManifest.model_validate(
        bus.request(build_dataset_message(purpose="exit-timing")).payload
    )


def test_train_predictor_writes_advisory_predictor() -> None:
    graph = InMemoryGraphStore()
    bus = _bind(graph)
    seed_narratives(graph, 6)
    dataset = _build(bus)

    manifest = PredictorManifest.model_validate(
        bus.request(train_predictor_message(purpose="exit-timing")).payload
    )

    assert manifest.advisory is True
    assert manifest.promotion_eligible is False
    assert "accuracy" in manifest.metrics
    assert manifest.sample_size == dataset.splits[2].example_count

    predictors = graph.list_nodes("Predictor")
    assert len(predictors) == 1
    edges = tuple(
        graph.descendants(predictors[0], max_depth=1, edge_types={"TRAINED_ON"})
    )
    assert len(edges) == 1
    assert edges[0].label == "Dataset"
    assert predictors[0].props["accuracy"] == manifest.metrics["accuracy"]


def test_second_train_increments_version() -> None:
    graph = InMemoryGraphStore()
    bus = _bind(graph)
    seed_narratives(graph, 6)
    _build(bus)

    bus.request(train_predictor_message(purpose="exit-timing"))
    second = PredictorManifest.model_validate(
        bus.request(train_predictor_message(purpose="exit-timing")).payload
    )

    assert second.predictor_id.endswith(":v2")
    assert len(graph.list_nodes("Predictor")) == 2


def test_train_predictor_no_dataset_degrades() -> None:
    graph = InMemoryGraphStore()
    bus = _bind(graph)

    manifest = PredictorManifest.model_validate(
        bus.request(train_predictor_message(purpose="exit-timing")).payload
    )

    assert manifest.sample_size == 0
    assert manifest.metrics == {}
    assert graph.list_nodes("Predictor") == ()


def test_train_split_too_small_degrades() -> None:
    graph = InMemoryGraphStore()
    bus = _bind(graph)
    seed_narratives(graph, 1)
    _build(bus)

    manifest = PredictorManifest.model_validate(
        bus.request(train_predictor_message(purpose="exit-timing")).payload
    )

    assert manifest.metrics == {}
    assert graph.list_nodes("Predictor") == ()


def test_train_predictor_degrades_on_graph_fault() -> None:
    bus = InProcessBus()
    sink = CollectingFaultSink()
    CuratorAgent(bus, graph=cast("GraphStore", _BrokenGraph()), sink=sink).bind()

    manifest = PredictorManifest.model_validate(
        bus.request(train_predictor_message(purpose="exit-timing")).payload
    )

    assert manifest.sample_size == 0
    assert len(sink.faults) == 1


class _BrokenGraph:
    def list_nodes(self, label: str) -> tuple[object, ...]:
        raise RuntimeError(label)
