"""P10 exit proof: build -> train -> promote through the registry.

Agent: curator
Role: prove the full promotion provenance chain and the no-decision-node boundary.
External I/O: none.
"""

from __future__ import annotations

from agents.curator.tests.helpers import (
    approve_flag,
    bind_curator_with_supervisor,
    build_dataset_message,
    promote,
    seed_narratives,
    train_predictor_message,
)
from kernel import InMemoryGraphStore, InProcessBus, Node

_PID = "predictor:exit-timing:exit_trigger:v1"

# Labels written by the curator registry flow or supervisor approval; everything
# else is decision/pipeline state the flow must never touch.
_REGISTRY_LABELS = frozenset(
    {
        "Dataset",
        "TrainingExample",
        "Predictor",
        "PredictorPromotion",
        "Flag",
        "FlagResolution",
    }
)
_DECISION_LABELS = ("Position", "TradeNarrative", "CloseDecision")


def _build_train_promote(graph: InMemoryGraphStore, bus: InProcessBus) -> None:
    bus.request(build_dataset_message(purpose="exit-timing"))
    bus.request(train_predictor_message(purpose="exit-timing"))
    promote(bus, _PID)  # pending_approval, raises the flag
    approve_flag(graph, _PID)  # operator approval stand-in
    promote(bus, _PID)  # promoted


def test_p10_exit_dataset_train_promote_with_provenance() -> None:
    """P10 exit: build -> train -> promote through the registry, full provenance."""
    graph = InMemoryGraphStore()
    bus = bind_curator_with_supervisor(graph)
    seed_narratives(graph, 60)

    bus.request(build_dataset_message(purpose="exit-timing"))
    bus.request(train_predictor_message(purpose="exit-timing"))
    pending = promote(bus, _PID)
    approve_flag(graph, _PID)
    result = promote(bus, _PID)

    assert pending.status == "pending_approval"
    assert result.status == "promoted"
    assert result.state == "load_bearing"

    promotion = graph.get_node("PredictorPromotion", f"promotion:{_PID}")
    assert promotion is not None
    predictor = _child(graph, promotion, "PROMOTES", "Predictor")
    dataset = _child(graph, predictor, "TRAINED_ON", "Dataset")
    example = _child(graph, dataset, "CONTAINS", "TrainingExample")
    narrative = _child(graph, example, "DERIVED_FROM", "TradeNarrative")
    assert narrative is not None


def test_p10_exit_promotion_mutates_no_decision_node() -> None:
    """The whole curator flow writes only curator + Flag/FlagResolution nodes."""
    graph = InMemoryGraphStore()
    bus = bind_curator_with_supervisor(graph)
    seed_narratives(graph, 60)

    before = _snapshot_non_registry(graph)
    _build_train_promote(graph, bus)
    after = _snapshot_non_registry(graph)

    assert after == before
    assert graph.get_node("PredictorPromotion", f"promotion:{_PID}") is not None


def _child(graph: InMemoryGraphStore, parent: Node, edge_type: str, label: str) -> Node:
    child = next(
        (
            node
            for node in graph.descendants(parent, max_depth=1, edge_types={edge_type})
            if node.label == label
        ),
        None,
    )
    assert child is not None, f"missing {label} via {edge_type}"
    return child


def _snapshot_non_registry(
    graph: InMemoryGraphStore,
) -> dict[tuple[str, str], object]:
    snapshot: dict[tuple[str, str], object] = {}
    for label in _DECISION_LABELS:
        for node in graph.list_nodes(label):
            assert label not in _REGISTRY_LABELS
            snapshot[(node.label, node.key)] = node.props
    return snapshot
