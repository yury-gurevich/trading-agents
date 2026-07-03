"""Curator served-entrypoint tests.

Agent: curator
Role: verify request-triggered serving builds curator-owned datasets only.
External I/O: none.
"""

from __future__ import annotations

from agents.curator.entrypoint import build_served_bus
from agents.curator.tests.helpers import build_dataset_message, seed_narratives
from contracts.curator import DatasetManifest
from kernel import InMemoryGraphStore
from kernel.serve_loop import LocalRequestConsumer, serve_once


def test_served_build_dataset_is_request_triggered_and_out_of_band() -> None:
    """CUR-TRG-02 / CUR-TRG-03 / CUR-NEV-01 / CUR-NEV-03: served build is isolated."""
    graph = InMemoryGraphStore()
    seed_narratives(graph, 6)
    decision_count = len(graph.list_nodes("CloseDecision"))
    bus = build_served_bus(graph)
    consumer = LocalRequestConsumer([build_dataset_message(purpose="s99-entrypoint")])

    served = serve_once(consumer, bus)

    assert served == 1
    assert len(consumer.replies) == 1
    manifest = DatasetManifest.model_validate(consumer.replies[0].payload)
    assert manifest.example_count == 6
    assert len(graph.list_nodes("Dataset")) == 1
    assert len(graph.list_nodes("TrainingExample")) == 6
    assert graph.list_nodes("OrderIntent") == ()
    assert graph.list_nodes("Recommendation") == ()
    assert len(graph.list_nodes("CloseDecision")) == decision_count
