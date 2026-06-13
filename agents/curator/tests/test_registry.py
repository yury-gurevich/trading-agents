"""Curator predictor-registry domain tests.

Agent: curator
Role: verify the evidence gate and graph-derived promotion status.
External I/O: none.
"""

from __future__ import annotations

from agents.curator.domain.registry import (
    check_promotion_evidence,
    is_promoted,
    promotion_status,
)
from agents.curator.settings import CuratorSettings
from kernel import InMemoryGraphStore, Node

_PID = "predictor:exit-timing:exit_trigger:v1"


def _predictor(accuracy: float, sample_size: int) -> Node:
    return Node("Predictor", _PID, {"accuracy": accuracy, "sample_size": sample_size})


def test_evidence_rejects_low_accuracy() -> None:
    ok, reason = check_promotion_evidence(_predictor(0.40, 10), CuratorSettings())
    assert ok is False
    assert "accuracy" in reason


def test_evidence_rejects_small_sample() -> None:
    ok, reason = check_promotion_evidence(_predictor(0.90, 2), CuratorSettings())
    assert ok is False
    assert "sample_size" in reason


def test_evidence_passes() -> None:
    ok, reason = check_promotion_evidence(_predictor(0.90, 10), CuratorSettings())
    assert ok is True
    assert reason == "evidence gate passed"


def test_status_advisory_by_default() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node("Predictor", _PID, {"accuracy": 0.9, "sample_size": 10})
    assert is_promoted(graph, _PID) is False
    assert promotion_status(graph, _PID) == "advisory"


def test_status_pending_after_flag() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node("Flag", f"flag:predictor:{_PID}:info", {"subject_ref": _PID})
    assert promotion_status(graph, _PID) == "pending_approval"


def test_status_advisory_when_flag_resolved() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node("Flag", f"flag:predictor:{_PID}:info", {})
    graph.merge_node("FlagResolution", f"resolution:flag:predictor:{_PID}:info", {})
    assert promotion_status(graph, _PID) == "advisory"


def test_status_load_bearing_after_promotion() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node("PredictorPromotion", f"promotion:{_PID}", {})
    assert is_promoted(graph, _PID) is True
    assert promotion_status(graph, _PID) == "load_bearing"
