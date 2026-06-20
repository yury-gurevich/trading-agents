"""P10 boundary test proving the curator never mutates a trading decision.

Agent: curator
Role: prove build_dataset is purely additive over curator labels, read-only elsewhere.
External I/O: none.
"""

from __future__ import annotations

from agents.curator import CuratorAgent
from agents.curator.tests.helpers import build_dataset_message, seed_narratives
from kernel import InMemoryGraphStore, InProcessBus

_CURATOR_LABELS = {"Dataset", "TrainingExample"}


def test_curator_build_dataset_mutates_no_decision_node() -> None:
    """CUR-NEV-01 / CUR-NEV-03: build_dataset writes only curator nodes;
    pre-existing nodes unchanged."""
    graph = InMemoryGraphStore()
    seed_narratives(graph, 6, trigger="time")
    bus = InProcessBus()
    CuratorAgent(bus, graph=graph).bind()

    before = _snapshot_non_curator_nodes(graph)
    bus.request(build_dataset_message(purpose="exit-timing"))
    after = _snapshot_non_curator_nodes(graph)

    assert after == before
    assert graph.list_nodes("Dataset")
    assert graph.list_nodes("TrainingExample")


def _snapshot_non_curator_nodes(
    graph: InMemoryGraphStore,
) -> dict[tuple[str, str], object]:
    snapshot: dict[tuple[str, str], object] = {}
    for label in ("Position", "TradeNarrative", "CloseDecision"):
        for node in graph.list_nodes(label):
            if node.label not in _CURATOR_LABELS:
                snapshot[(node.label, node.key)] = node.props
    return snapshot
