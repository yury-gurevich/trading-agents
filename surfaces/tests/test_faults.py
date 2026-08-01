"""Fault surface query tests.

Agent: surfaces
Role: verify incident projections from supervisor Fault nodes.
External I/O: none.
"""

from __future__ import annotations

from kernel import InMemoryGraphStore
from kernel.fault_graph import FAULT_SUPPRESSION_LABEL
from surfaces.queries import open_faults
from surfaces.queries.faults import FaultView
from surfaces.render_extras import render_incidents


def test_open_faults_handles_empty_graph() -> None:
    assert open_faults(InMemoryGraphStore()) == ()


def test_open_faults_returns_newest_faults_first() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node(
        "Fault",
        "fault:old:abcdef",
        {
            "source_agent": "scanner",
            "capability": "scan",
            "severity": "warn",
            "message": "old fault",
            "occurred_at": "2026-06-10T00:00:00+00:00",
        },
    )
    graph.merge_node(
        "Fault",
        "fault:new:abcdef",
        {
            "source_agent": "analyst",
            "capability": "analyze",
            "severity": "critical",
            "message": "new fault",
            "occurred_at": "2026-06-11T00:00:00+00:00",
        },
    )

    faults = open_faults(graph)

    assert [fault.source_agent for fault in faults] == ["analyst", "scanner"]
    assert faults[0].fault_id == "fault:new:ab"
    assert faults[0].message == "new fault"


def test_open_faults_ignores_malformed_suppression_summary() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node(
        "Fault",
        "fault:old:abcdef",
        {
            "source_agent": "scanner",
            "capability": "scan",
            "severity": "warn",
            "message": "old fault",
            "occurred_at": "2026-06-10T00:00:00+00:00",
        },
    )
    graph.merge_node(
        FAULT_SUPPRESSION_LABEL,
        "fault-suppression:missing-link",
        {"occurrence_count": 5, "suppressed_count": 4},
    )

    faults = open_faults(graph)

    assert faults[0].occurrence_count == 1
    assert faults[0].suppressed_count == 0


def test_render_incidents_continues_after_unsuppressed_fault() -> None:
    faults = (
        FaultView(
            fault_id="fault:one",
            source_agent="scanner",
            capability="scan",
            severity="warn",
            message="first",
            occurred_at="2026-06-10T00:00:00+00:00",
        ),
        FaultView(
            fault_id="fault:two",
            source_agent="execution",
            capability="position_sync",
            severity="critical",
            message="second",
            occurred_at="2026-06-10T00:01:00+00:00",
            occurrence_count=3,
            suppressed_count=2,
        ),
    )

    rendered = render_incidents(faults)

    assert "[fault:one]" in rendered
    assert "[fault:two]" in rendered
    assert "occurrences: 3 (suppressed 2)" in rendered
