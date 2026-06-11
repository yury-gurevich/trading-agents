"""Researcher evidence reducer tests.

Agent: researcher
Role: verify Snapshot metrics become bounded research evidence.
External I/O: none.
"""

from __future__ import annotations

from agents.researcher.domain.evidence import collect_evidence
from kernel import InMemoryGraphStore


def test_collect_evidence_requires_minimum_samples() -> None:
    graph = InMemoryGraphStore()
    assert collect_evidence(graph, min_sample_runs=5) is None
    for index in range(4):
        _snapshot(graph, index)
    assert collect_evidence(graph, min_sample_runs=5) is None


def test_collect_evidence_averages_snapshot_metrics() -> None:
    graph = InMemoryGraphStore()
    for index in range(5):
        _snapshot(graph, index, confidence=0.35, approval=0.80, rejected=1.0)

    evidence = collect_evidence(graph, min_sample_runs=5)

    assert evidence is not None
    assert evidence.snapshot_count == 5
    assert evidence.avg_confidence == 0.35
    assert evidence.avg_approval_rate == 0.80
    assert evidence.avg_rejection_count == 1.0


def test_collect_evidence_treats_bad_metrics_as_zero() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node("Snapshot", "snapshot:bad-metrics", {"metrics": "bad"})
    graph.merge_node("Snapshot", "snapshot:bad-signal", {"metrics": {"signal": "bad"}})
    graph.merge_node(
        "Snapshot",
        "snapshot:bad-number",
        {"metrics": {"signal": {"avg_confidence": "bad"}}},
    )
    graph.merge_node(
        "Snapshot",
        "snapshot:none-number",
        {"metrics": {"signal": {"avg_confidence": None}}},
    )
    for index in range(2):
        _snapshot(graph, index, confidence=0.25)

    evidence = collect_evidence(graph, min_sample_runs=5)

    assert evidence is not None
    assert evidence.avg_confidence == (0.25 * 2) / 6


def _snapshot(
    graph: InMemoryGraphStore,
    index: int,
    *,
    confidence: float = 0.35,
    approval: float = 0.80,
    rejected: float = 1.0,
) -> None:
    graph.merge_node(
        "Snapshot",
        f"snapshot:run-{index}",
        {
            "run_id": f"run-{index}",
            "metrics": {
                "portfolio": {"approval_rate": approval},
                "signal": {
                    "avg_confidence": confidence,
                    "rejection_count": rejected,
                },
            },
            "headline_summary": "test run",
        },
    )
