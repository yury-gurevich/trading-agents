"""Surface health incident tests.

Agent: surfaces
Role: verify dashboard health shares the supervisor Fault incident predicate.
External I/O: none.
"""

from __future__ import annotations

from agents.supervisor.domain.health import compute_health
from kernel import InMemoryGraphStore
from surfaces.queries import system_health


def test_system_health_agrees_with_supervisor_fault_incident_scope() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node(
        "BrokerPositionSnapshot",
        "broker-position-snapshot:current",
        {"created_at": "2026-08-18T04:00:00+00:00"},
    )
    graph.merge_node(
        "Fault",
        "fault:old-error",
        {
            "status": "pending",
            "severity": "error",
            "occurred_at": "2026-07-30T22:30:00+00:00",
        },
    )
    graph.merge_node(
        "Fault",
        "fault:current-warning",
        {
            "status": "pending",
            "severity": "warning",
            "occurred_at": "2026-08-18T04:20:00+00:00",
        },
    )
    graph.merge_node(
        "Fault",
        "fault:current-error",
        {
            "status": "pending",
            "severity": "error",
            "occurred_at": "2026-08-18T04:22:00+00:00",
        },
    )

    supervisor_health = compute_health(graph, None)
    surface_health = system_health(graph)

    assert supervisor_health["open_incidents"] == 1
    assert surface_health.open_faults == supervisor_health["open_incidents"]
    assert surface_health.healthy == supervisor_health["healthy"]
