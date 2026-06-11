"""Fault surface query tests.

Agent: surfaces
Role: verify incident projections from supervisor Fault nodes.
External I/O: none.
"""

from __future__ import annotations

from kernel import InMemoryGraphStore
from surfaces.queries import open_faults


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
