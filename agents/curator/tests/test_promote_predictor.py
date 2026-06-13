"""Curator promote_predictor bus tests.

Agent: curator
Role: verify the evidence gate, flag-then-approve flow, idempotency, and unknowns.
External I/O: none.
"""

from __future__ import annotations

from typing import cast

from agents.curator import CuratorAgent
from agents.curator.tests.helpers import (
    approve_flag,
    bind_curator_with_supervisor,
    promote,
)
from kernel import CollectingFaultSink, GraphStore, InMemoryGraphStore, InProcessBus

_PID = "predictor:exit-timing:exit_trigger:v1"


def _seed_predictor(graph: InMemoryGraphStore, *, accuracy: float, n: int) -> None:
    graph.merge_node(
        "Predictor",
        _PID,
        {
            "purpose": "exit-timing",
            "target": "exit_trigger",
            "strategy": "majority_class",
            "accuracy": accuracy,
            "sample_size": n,
            "advisory": True,
        },
    )


def test_low_accuracy_rejected_without_flag() -> None:
    graph = InMemoryGraphStore()
    bus = bind_curator_with_supervisor(graph)
    _seed_predictor(graph, accuracy=0.40, n=10)

    result = promote(bus, _PID)

    assert result.status == "rejected"
    assert result.state == "advisory"
    assert graph.list_nodes("Flag") == ()
    assert graph.list_nodes("PredictorPromotion") == ()


def test_passing_evidence_first_call_pends_with_flag() -> None:
    graph = InMemoryGraphStore()
    bus = bind_curator_with_supervisor(graph)
    _seed_predictor(graph, accuracy=0.90, n=10)

    result = promote(bus, _PID)

    assert result.status == "pending_approval"
    assert result.state == "advisory"
    flags = graph.list_nodes("Flag")
    assert len(flags) == 1
    assert flags[0].props["subject_ref"] == f"predictor:{_PID}"
    assert graph.list_nodes("PredictorPromotion") == ()


def test_promote_after_approval_writes_audit() -> None:
    graph = InMemoryGraphStore()
    bus = bind_curator_with_supervisor(graph)
    _seed_predictor(graph, accuracy=0.90, n=10)

    promote(bus, _PID)
    approve_flag(graph, _PID)
    result = promote(bus, _PID)

    assert result.status == "promoted"
    assert result.state == "load_bearing"
    promotions = graph.list_nodes("PredictorPromotion")
    assert len(promotions) == 1
    assert promotions[0].props["accuracy"] == 0.90
    assert promotions[0].props["sample_size"] == 10
    edges = tuple(
        graph.descendants(promotions[0], max_depth=1, edge_types={"PROMOTES"})
    )
    assert len(edges) == 1
    assert edges[0].key == _PID


def test_re_promotion_is_idempotent() -> None:
    graph = InMemoryGraphStore()
    bus = bind_curator_with_supervisor(graph)
    _seed_predictor(graph, accuracy=0.90, n=10)

    promote(bus, _PID)
    approve_flag(graph, _PID)
    promote(bus, _PID)
    result = promote(bus, _PID)

    assert result.status == "already_promoted"
    assert result.state == "load_bearing"
    assert len(graph.list_nodes("PredictorPromotion")) == 1


def test_unknown_predictor_not_found() -> None:
    graph = InMemoryGraphStore()
    bus = bind_curator_with_supervisor(graph)

    result = promote(bus, "predictor:missing:exit_trigger:v9")

    assert result.status == "not_found"
    assert result.state == "advisory"


def test_second_pending_call_does_not_reflag() -> None:
    graph = InMemoryGraphStore()
    bus = bind_curator_with_supervisor(graph)
    _seed_predictor(graph, accuracy=0.90, n=10)

    first = promote(bus, _PID)
    second = promote(bus, _PID)

    assert first.status == "pending_approval"
    assert second.status == "pending_approval"
    assert len(graph.list_nodes("Flag")) == 1


def test_promote_degrades_on_graph_fault() -> None:
    bus = InProcessBus()
    sink = CollectingFaultSink()
    CuratorAgent(bus, graph=cast("GraphStore", _BrokenGraph()), sink=sink).bind()

    result = promote(bus, _PID)

    assert result.status == "rejected"
    assert result.reason == "promotion fault"
    assert len(sink.faults) == 1


class _BrokenGraph:
    def get_node(self, label: str, key: str) -> object:
        raise RuntimeError(f"{label}:{key}")
