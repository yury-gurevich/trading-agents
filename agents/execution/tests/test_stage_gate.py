"""Execution stage-gate domain tests.

Agent: execution
Role: verify evidence reduction, transition ordering, and stage lookup.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.domain.stage_gate import (
    StageEvidence,
    check_promotion_allowed,
    collect_stage_evidence,
    is_valid_demotion,
    is_valid_promotion,
)
from agents.execution.settings import ExecutionSettings
from agents.execution.store import current_stage_from_graph, write_stage_transition
from agents.execution.tests.stage_helpers import seed_stage_snapshots
from kernel import InMemoryGraphStore


def test_promotion_allowed_rejects_missing_runs_low_rate_and_faults() -> None:
    settings = ExecutionSettings()
    assert check_promotion_allowed(StageEvidence(0, 0.0, 0), settings)[0] is False
    assert (
        "need 10 runs" in check_promotion_allowed(StageEvidence(0, 0.0, 0), settings)[1]
    )
    assert check_promotion_allowed(StageEvidence(10, 0.50, 0), settings)[0] is False
    assert check_promotion_allowed(StageEvidence(10, 0.80, 1), settings)[0] is False
    assert check_promotion_allowed(StageEvidence(10, 0.80, 0), settings) == (
        True,
        "evidence gate passed",
    )


def test_stage_order_allows_single_step_promotion_and_any_demotion() -> None:
    assert is_valid_promotion("paper", "broker_shadow") is True
    assert is_valid_promotion("paper", "live_manual") is False
    assert is_valid_promotion("live_manual", "live_autopilot") is False
    assert is_valid_demotion("broker_shadow", "paper") is True
    assert is_valid_demotion("paper", "broker_shadow") is False


def test_collect_stage_evidence_from_snapshots_and_faults() -> None:
    graph = InMemoryGraphStore()
    seed_stage_snapshots(graph, approval_rate=0.80)
    graph.merge_node("Fault", "fault:critical", {"severity": "critical"})
    graph.merge_node("Fault", "fault:warn", {"severity": "warn"})

    evidence = collect_stage_evidence(graph)

    assert evidence.snapshot_count == 10
    assert evidence.avg_approval_rate == 0.80
    assert evidence.critical_fault_count == 1


def test_collect_stage_evidence_treats_bad_metrics_as_zero() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node("Snapshot", "snapshot:bad-metrics", {"metrics": "bad"})
    graph.merge_node(
        "Snapshot", "snapshot:bad-portfolio", {"metrics": {"portfolio": []}}
    )
    graph.merge_node(
        "Snapshot",
        "snapshot:bad-number",
        {"metrics": {"portfolio": {"approval_rate": object()}}},
    )
    graph.merge_node(
        "Snapshot",
        "snapshot:bad-string",
        {"metrics": {"portfolio": {"approval_rate": "bad"}}},
    )

    evidence = collect_stage_evidence(graph)

    assert evidence.avg_approval_rate == 0.0


def test_current_stage_from_graph_falls_back_and_reads_latest_transition() -> None:
    graph = InMemoryGraphStore()
    assert current_stage_from_graph(graph, "paper") == "paper"
    write_stage_transition(
        graph, from_stage="paper", to_stage="broker_shadow", reason="ok"
    )
    assert current_stage_from_graph(graph, "paper") == "broker_shadow"
    graph.merge_node(
        "StageTransition",
        "stage:bad",
        {"to_stage": "bad", "transitioned_at": "9999"},
    )
    assert current_stage_from_graph(graph, "paper") == "paper"
