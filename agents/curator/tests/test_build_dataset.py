"""Curator build_dataset bus tests.

Agent: curator
Role: verify build_dataset writes curator nodes, versions, and a store payload.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from agents.curator import CuratorAgent
from agents.curator.dataset_store import FakeDatasetStore
from agents.curator.tests.helpers import (
    build_dataset_message,
    describe_corpus_message,
    seed_narratives,
)
from contracts.common import Explanation
from contracts.curator import DatasetManifest
from kernel import CollectingFaultSink, InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from kernel import GraphStore


def _bind(graph: InMemoryGraphStore, store: FakeDatasetStore) -> InProcessBus:
    bus = InProcessBus()
    CuratorAgent(bus, graph=graph, dataset_store=store).bind()
    return bus


def test_build_dataset_writes_nodes_edges_and_payload() -> None:
    """CUR-IN-01 / CUR-TRG-01 / CUR-OUT-01 / CUR-IDN-02: build_dataset → manifest +
    Dataset/TrainingExample nodes."""
    graph = InMemoryGraphStore()
    store = FakeDatasetStore()
    bus = _bind(graph, store)
    seed_narratives(graph, 6)

    manifest = DatasetManifest.model_validate(
        bus.request(build_dataset_message(purpose="exit-timing")).payload
    )

    assert manifest.version == 1
    assert manifest.example_count == 6
    assert len(graph.list_nodes("Dataset")) == 1
    assert len(graph.list_nodes("TrainingExample")) == 6
    assert store.written.keys() == {manifest.dataset_id}


def test_build_dataset_links_examples_to_sources() -> None:
    graph = InMemoryGraphStore()
    bus = _bind(graph, FakeDatasetStore())
    seed_narratives(graph, 6)

    bus.request(build_dataset_message(purpose="exit-timing"))

    dataset = graph.list_nodes("Dataset")[0]
    contained = graph.descendants(dataset, max_depth=1, edge_types={"CONTAINS"})
    examples = tuple(contained)
    assert len(examples) == 6
    for example in examples:
        sources = tuple(
            graph.descendants(example, max_depth=1, edge_types={"DERIVED_FROM"})
        )
        assert len(sources) == 1
        assert sources[0].label == "TradeNarrative"


def test_second_build_increments_version() -> None:
    """CUR-IDM-02: re-running build_dataset increments version; not idempotent."""
    graph = InMemoryGraphStore()
    bus = _bind(graph, FakeDatasetStore())
    seed_narratives(graph, 6)

    bus.request(build_dataset_message(purpose="exit-timing"))
    second = DatasetManifest.model_validate(
        bus.request(build_dataset_message(purpose="exit-timing")).payload
    )

    assert second.version == 2


def test_empty_corpus_degrades_without_crash() -> None:
    """CUR-FAIL-05 / CUR-NEV-04: empty corpus → manifest with 0 examples;
    no crash; Dataset node written."""
    graph = InMemoryGraphStore()
    bus = _bind(graph, FakeDatasetStore())

    manifest = DatasetManifest.model_validate(
        bus.request(build_dataset_message(purpose="exit-timing")).payload
    )

    assert manifest.example_count == 0
    assert len(graph.list_nodes("Dataset")) == 1


def test_describe_corpus_summarises_counts() -> None:
    """CUR-IN-02 / CUR-OUT-02: describe_corpus returns Explanation; no graph write."""
    graph = InMemoryGraphStore()
    bus = _bind(graph, FakeDatasetStore())
    seed_narratives(graph, 6)

    explanation = Explanation.model_validate(
        bus.request(describe_corpus_message(purpose="exit-timing")).payload
    )
    empty = Explanation.model_validate(
        bus.request(describe_corpus_message(purpose="x")).payload
    )

    assert "6 completed-trade narratives" in explanation.summary
    assert "6 completed-trade narratives" in empty.summary


def test_describe_empty_corpus_reports_nothing_collected() -> None:
    bus = _bind(InMemoryGraphStore(), FakeDatasetStore())

    explanation = Explanation.model_validate(
        bus.request(describe_corpus_message(purpose="exit-timing")).payload
    )

    assert explanation.summary == "no training corpus collected yet"


def test_build_dataset_degrades_on_graph_fault() -> None:
    bus = InProcessBus()
    sink = CollectingFaultSink()
    CuratorAgent(bus, graph=cast("GraphStore", _BrokenGraph()), sink=sink).bind()

    manifest = DatasetManifest.model_validate(
        bus.request(build_dataset_message(purpose="exit-timing")).payload
    )

    assert manifest.example_count == 0
    assert manifest.version == 1
    assert len(sink.faults) == 1


class _BrokenGraph:
    def list_nodes(self, label: str) -> tuple[object, ...]:
        raise RuntimeError(label)
