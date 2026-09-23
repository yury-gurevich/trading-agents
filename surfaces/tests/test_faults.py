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
from surfaces.queries.health import system_health
from surfaces.render_extras import render_incidents


def test_open_faults_handles_empty_graph() -> None:
    assert open_faults(InMemoryGraphStore()) == ()


def test_open_faults_lists_only_live_incidents_newest_first() -> None:
    """Warnings, older run days and resolved faults are history, not incidents.

    The list must be exactly what health counts: it once dumped every fault
    ever raised (6,439) while health reported 0 open incidents.
    """
    graph = InMemoryGraphStore()
    _fault(graph, "fault:old:abcdef", "scanner", "error", "2026-06-10T23:00:00")
    _fault(graph, "fault:warn:abcdef", "monitor", "warn", "2026-06-11T00:30:00")
    _fault(graph, "fault:done:abcdef", "execution", "critical", "2026-06-11T00:45:00")
    graph.merge_node("FaultResolution", "fr:done", {"fault_key": "fault:done:abcdef"})
    _fault(graph, "fault:early:abcdef", "provider", "error", "2026-06-11T00:10:00")
    _fault(graph, "fault:new:abcdef", "analyst", "critical", "2026-06-11T01:00:00")

    faults = open_faults(graph)

    assert [fault.source_agent for fault in faults] == ["analyst", "provider"]
    assert faults[0].fault_id == "fault:new:ab"
    assert faults[0].message == "analyst fault"
    assert system_health(graph).open_faults == len(faults)


def _fault(
    graph: InMemoryGraphStore, key: str, agent: str, severity: str, at: str
) -> None:
    graph.merge_node(
        "Fault",
        key,
        {
            "source_agent": agent,
            "capability": "work",
            "severity": severity,
            "message": f"{agent} fault",
            "occurred_at": f"{at}+00:00",
        },
    )


def test_open_faults_ignores_malformed_suppression_summary() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node(
        "Fault",
        "fault:old:abcdef",
        {
            "source_agent": "scanner",
            "capability": "scan",
            "severity": "error",
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
