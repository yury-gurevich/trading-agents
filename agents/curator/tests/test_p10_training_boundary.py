"""P10 boundary test proving train_predictor mutates no prior node.

Agent: curator
Role: prove train_predictor is purely additive over Predictor, read-only elsewhere.
External I/O: none.
"""

from __future__ import annotations

from agents.curator import CuratorAgent
from agents.curator.tests.helpers import (
    build_dataset_message,
    seed_narratives,
    train_predictor_message,
)
from kernel import InMemoryGraphStore, InProcessBus

_NON_PREDICTOR_LABELS = (
    "Position",
    "TradeNarrative",
    "CloseDecision",
    "Dataset",
    "TrainingExample",
)


def test_train_predictor_mutates_no_prior_node() -> None:
    """Every non-Predictor node is identical before and after training."""
    graph = InMemoryGraphStore()
    bus = InProcessBus()
    CuratorAgent(bus, graph=graph).bind()
    seed_narratives(graph, 6)
    bus.request(build_dataset_message(purpose="exit-timing"))

    before = _snapshot(graph)
    bus.request(train_predictor_message(purpose="exit-timing"))
    after = _snapshot(graph)

    assert after == before
    assert graph.list_nodes("Predictor")


def _snapshot(graph: InMemoryGraphStore) -> dict[tuple[str, str], object]:
    snapshot: dict[tuple[str, str], object] = {}
    for label in _NON_PREDICTOR_LABELS:
        for node in graph.list_nodes(label):
            snapshot[(node.label, node.key)] = node.props
    return snapshot
